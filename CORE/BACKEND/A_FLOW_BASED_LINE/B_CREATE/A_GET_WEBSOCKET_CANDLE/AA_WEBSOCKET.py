import websocket
import json
import yaml
import sys
import signal
from datetime import datetime, timezone
import threading
import time
from typing import Dict, Any, Optional
import os
import re
import random

# =========================
# Settings (edit here)
# =========================
# Raw stream base (we construct /ws/<symbol@kline_interval>)
WS_BASE_WS = "wss://fstream.binance.com/ws"

FILE_PATH = "CORE/DATA/AA_CANDLE.yaml"
SETTINGS_PATH = "CORE/DATA/BB_USER_SETTINGS.yaml"

BEFORE_SCRIPTS = [
    "CORE/BACKEND/A_FLOW_BASED_LINE/A_RESET/CHECK_IF_NEED_RESET.py",
]

THE_MAIN_SCRIPTS = [
    "CORE/BACKEND/A_FLOW_BASED_LINE/C_CHECK/RUN_LIST.py",
]

# Heartbeat and reconnect/backoff settings
PING_INTERVAL = 15            # seconds between pings sent by client
PING_TIMEOUT = 10             # seconds to wait for pong
BACKOFF_BASE_SECONDS = 1      # initial backoff
BACKOFF_MAX_SECONDS = 60      # cap for exponential backoff
JITTER_MAX_MS = 500           # add random jitter up to N ms

DEBUG_MODE = False  # Set True to enable debug prints
# =========================


# -------- Internal state (do not edit) --------
USER_INTERRUPT_REASON = "🔧  Остановлено пользователем (Ctrl+C)"

last_execution_start_time = None
stop_reason = None
LAST_FINALIZE_REASON = None

previous_settings = {
    "SYSTEM_TIMEFRAME": None,
    "SYSTEM_SYMBOL": None,
}

candles: Dict[str, Dict[str, Any]] = {}
candles_lock = threading.Lock()

# Processing signaling
process_event = threading.Event()
process_thread: Optional[threading.Thread] = None
process_lock = threading.Lock()  # guards creation/join of process_thread
main_run_active = threading.Event()  # marks main scripts execution in progress

settings_monitor_active = False
restart_timer_active = False

current_ws = None
monitor_thread = None
timer_thread = None

shutdown_event = threading.Event()     # global shutdown flag
FINALIZED = threading.Event()          # guard to prevent double finalize()

# Supported values
SUPPORTED_TIMEFRAMES = {
    "1m", "3m", "5m", "15m", "30m",
    "1h", "2h", "4h", "6h", "8h", "12h",
    "1d", "3d", "1w", "1M"
}
SYMBOL_SUFFIXES = ("USDT", "BUSD", "USD", "USDC", "TUSD", "FDUSD")


# =========================
# Utilities
# =========================
class RealTimeCapture:
    """Capture stdout/stderr and print in real-time without prefixes."""
    def __init__(self, script_name: str, original_stream):
        self.script_name = script_name
        self.original_stream = original_stream

    def write(self, text):
        # Print only non-empty lines as-is
        if text:
            for line in text.splitlines(keepends=True):
                if line.strip():
                    self.original_stream.write(line.rstrip() + "\n")
                    self.original_stream.flush()
        return len(text)

    def flush(self):
        self.original_stream.flush()


def debug_print(msg: str):
    if DEBUG_MODE:
        print(f"DEBUG: {msg}")


def log_error(kind: str, err: Exception, context: str = ""):
    """Unified errors logger."""
    if isinstance(err, KeyboardInterrupt):
        return
    ctx = f" ({context})" if context else ""
    print(f"{kind}{ctx}: {err}")
    debug_print(f"{kind}{ctx} -> {type(err).__name__}")


def show_last_execution_time():
    """Print duration of the last main-scripts iteration if running."""
    global last_execution_start_time
    if last_execution_start_time is not None:
        dt = time.time() - last_execution_start_time
        print(f"🔧  - {dt:.3f} СЕКУНД ")


def safe_join(th: threading.Thread, timeout: float = None):
    if th and th.is_alive():
        th.join(timeout=timeout)


def responsive_sleep(seconds: float):
    """Sleep in small steps; break early if shutdown requested."""
    steps = max(1, int(seconds * 10))
    for _ in range(steps):
        if shutdown_event.is_set():
            return
        time.sleep(0.1)


def atomic_yaml_dump(path: str, data: Any):
    """Write YAML atomically using temp file + os.replace."""
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        yaml.dump(data, f, sort_keys=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def reset_candles(clear_file: bool):
    """Reset candles both on disk (optional) and in-memory."""
    try:
        if clear_file and os.path.exists(FILE_PATH):
            atomic_yaml_dump(FILE_PATH, {})
            print("🧹 Файл свечей очищен из-за изменения настроек")
        with candles_lock:
            candles.clear()
        debug_print("Candles cleared")
    except Exception as e:
        log_error("Ошибка очистки свечей", e, FILE_PATH)


def finalize(reason: str, ws: websocket.WebSocketApp = None, shutdown_for_exit: bool = False):
    """
    Graceful finalize:
      1) close WS,
      2) if main scripts are running, wait until they finish,
      3) optionally set shutdown_event and join process thread (for hard exits).
    """
    global stop_reason, LAST_FINALIZE_REASON
    if FINALIZED.is_set():
        return
    FINALIZED.set()

    stop_reason = reason
    LAST_FINALIZE_REASON = reason

    # Stop monitors/timers flags first
    global settings_monitor_active, restart_timer_active
    settings_monitor_active = False
    restart_timer_active = False

    # Try to close WS gently
    if ws is not None:
        try:
            ws.keep_running = False
            ws.close()
        except Exception as e:
            log_error("WebSocket ошибка при закрытии", e)

    # If main scripts are running, wait for them to complete
    # (do not spin forever; rely on them to finish)
    while main_run_active.is_set():
        time.sleep(0.05)

    # For hard exits (Ctrl+C or critical fatal), terminate background loop
    if shutdown_for_exit:
        shutdown_event.set()

    # Wait processing thread if we are shutting down fully
    with process_lock:
        if shutdown_for_exit and process_thread and process_thread.is_alive():
            safe_join(process_thread)

    print(reason)
    # leave stop_reason intact only for user-facing printing; runtime uses LAST_FINALIZE_REASON


def build_output(candles_flat: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build YAML structure:
    BINANCE_FUTURES:
      - <SYMBOL>:
        - <TIMEFRAME>:
          - CANDLE: 0
            CLOSE_TIME: ...
            TIMESTAMP: ...
            OPEN_TIME: ...
            HIGH_PRICE: ...
            CLOSE_PRICE: ...
            OPEN_PRICE: ...
            LOW_PRICE: ...
    Note: "CANDLE" is fixed to 0 to mirror the requested example.
    """
    # Group by symbol and timeframe
    symbol_groups: Dict[str, Dict[str, list]] = {}
    for key, payload in candles_flat.items():
        # Expect key format: "<SYMBOL>_<TIMEFRAME>"
        if "_" in key:
            symbol, timeframe = key.rsplit("_", 1)
        else:
            symbol, timeframe = key, globals().get("SYSTEM_TIMEFRAME", "1m")

        item = {"CANDLE": 0}
        item.update(payload)

        symbol_groups.setdefault(symbol, {}).setdefault(timeframe, []).append(item)

    root_list = []
    for symbol, tf_map in symbol_groups.items():
        tf_list = []
        for timeframe, items in tf_map.items():
            tf_list.append({timeframe: items})
        root_list.append({symbol: tf_list})

    return {"BINANCE_FUTURES": root_list}


# =========================
# Settings / Validation
# =========================
def load_settings() -> Dict[str, Any]:
    """Load YAML settings."""
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            s = yaml.safe_load(f) or {}
        debug_print("Settings loaded")
        return s
    except FileNotFoundError:
        msg = f"Файл настроек {SETTINGS_PATH} не найден"
        print(msg)
        raise
    except yaml.YAMLError as e:
        log_error("Ошибка чтения настроек из YAML", e)
        raise
    except Exception as e:
        log_error("Ошибка загрузки настроек", e)
        raise


def extract_symbol(settings: Dict[str, Any]) -> str:
    """
    Prefer SYSTEM_SYMBOL (string). For backward compatibility,
    fall back to WEBSOCKET_SYMBOL (list) and take the first element.
    Enforce single pair.
    """
    sym = settings.get("SYSTEM_SYMBOL")
    if sym:
        if isinstance(sym, str):
            return sym.strip().upper()
        else:
            raise ValueError("SYSTEM_SYMBOL должен быть строкой")
    # Backward-compat branch
    ws_list = settings.get("WEBSOCKET_SYMBOL")
    if isinstance(ws_list, list) and ws_list:
        if len(ws_list) > 1:
            print(f"⚠ Найдено более 1 символа в WEBSOCKET_SYMBOL, беру первый: {ws_list[0]}")
        return str(ws_list[0]).strip().upper()
    raise ValueError("Не задан SYSTEM_SYMBOL и отсутствует валидный WEBSOCKET_SYMBOL")


def validate_settings(current: Dict[str, Any]) -> Dict[str, Any]:
    """Validate timeframe and symbol; return normalized settings dict."""
    tf = current.get("SYSTEM_TIMEFRAME")
    if tf is None:
        raise ValueError("SYSTEM_TIMEFRAME отсутствует в настройках")
    if tf not in SUPPORTED_TIMEFRAMES:
        raise ValueError(f"Неподдерживаемый таймфрейм: {tf}. Разрешено: {sorted(SUPPORTED_TIMEFRAMES)}")

    symbol = extract_symbol(current)
    # Basic symbol validation: uppercase letters/digits; usually ends with known quote asset
    if not re.match(r"^[A-Z0-9]{3,30}$", symbol):
        raise ValueError(f"Некорректный символ: {symbol}")
    if not symbol.endswith(SYMBOL_SUFFIXES):
        print(f"⚠ Символ {symbol} не оканчивается на типичный суффикс {SYMBOL_SUFFIXES}. Продолжаю, но проверь символ.")

    restart_interval = current.get("WEBSOCKET_RESTART_INTERVAL", 55)  # minutes; default safe under 24h

    return {
        "SYSTEM_TIMEFRAME": tf,
        "SYSTEM_SYMBOL": symbol,
        "WEBSOCKET_RESTART_INTERVAL": int(restart_interval),
    }


def check_settings_changes(validated: Dict[str, Any]):
    """Detect changes vs previous_settings (symbol/timeframe)."""
    tf = validated["SYSTEM_TIMEFRAME"]
    symbol = validated["SYSTEM_SYMBOL"]

    tf_changed = (previous_settings["SYSTEM_TIMEFRAME"] not in (None, tf)
                  and previous_settings["SYSTEM_TIMEFRAME"] != tf)
    sym_changed = (previous_settings["SYSTEM_SYMBOL"] not in (None, symbol)
                   and previous_settings["SYSTEM_SYMBOL"] != symbol)

    if tf_changed:
        print(f"🔄 Изменен таймфрейм: {previous_settings['SYSTEM_TIMEFRAME']} → {tf}")
    if sym_changed:
        print(f"🔄 Изменен символ: {previous_settings['SYSTEM_SYMBOL']} → {symbol}")

    previous_settings["SYSTEM_TIMEFRAME"] = tf
    previous_settings["SYSTEM_SYMBOL"] = symbol

    needs_restart = tf_changed or sym_changed
    needs_file_clear = needs_restart
    return needs_restart, needs_file_clear


# =========================
# I/O + Scripts
# =========================
def execute_scripts(scripts_list, description: str, finish_if_started: bool = False):
    """
    Exec a list of Python scripts with real-time output passthrough.
    If finish_if_started=True, ignore shutdown_event once started (to complete the batch).
    """
    global last_execution_start_time
    started = time.time()
    if description == "основных скриптов":
        last_execution_start_time = started

    # Mark that main scripts execution is in progress (for finalize waiting)
    if description == "основных скриптов":
        main_run_active.set()

    try:
        for script in scripts_list:
            # Respect shutdown only for non-mandatory completion runs
            if shutdown_event.is_set() and not finish_if_started:
                break

            try:
                try:
                    with open(script, "r", encoding="utf-8") as f:
                        code = f.read()
                except FileNotFoundError:
                    print(f"Скрипт {script} не найден")
                    continue
                except Exception as e:
                    print(f"Ошибка чтения скрипта {script}: {e}")
                    continue

                script_name = script.rsplit("/", 1)[-1]

                # Prepare isolated globals for the script
                script_globals = {"__name__": "__main__", "__file__": script}

                # Capture stdout/stderr live
                old_out, old_err = sys.stdout, sys.stderr
                sys.stdout = RealTimeCapture(script_name, old_out)
                sys.stderr = RealTimeCapture(f"{script_name}[ERROR]", old_err)

                try:
                    exec(code, script_globals)
                except KeyboardInterrupt:
                    # Propagate to main loop for unified finalize
                    raise
                except Exception as e:
                    # Use original stderr to print execution errors
                    old_err.write(f"[{script_name}[ERROR]] Ошибка выполнения: {e}")
                    old_err.flush()
                finally:
                    sys.stdout, sys.stderr = old_out, old_err

            except KeyboardInterrupt:
                raise
            except Exception as e:
                log_error("Ошибка выполнения скрипта", e, script)

    finally:
        if description == "основных скриптов":
            print(f"⚡ - {time.time() - started:.3f} СЕКУНД")
            last_execution_start_time = None
            main_run_active.clear()


# =========================
# WebSocket flow
# =========================
def process_loop():
    """Background loop: wait for signal, save YAML atomically, then run scripts."""
    debug_print("Start process loop")
    try:
        while not shutdown_event.is_set():
            # Wait until there is something to process
            triggered = process_event.wait(timeout=1.0)
            if not triggered:
                continue
            process_event.clear()

            try:
                with candles_lock:
                    current = {k: v.copy() for k, v in candles.items()}

                formatted = build_output(current)
                atomic_yaml_dump(FILE_PATH, formatted)
                debug_print(f"Saved atomically to {FILE_PATH}")

                if shutdown_event.is_set():
                    # Even if shutting down, we will still run THE_MAIN_SCRIPTS if requested to finish
                    pass

                # Run THE_MAIN_SCRIPTS and finish them if already started
                execute_scripts(THE_MAIN_SCRIPTS, "основных скриптов", finish_if_started=True)

            except Exception as e:
                print(f"Неожиданная ошибка в process_loop: {e}")
                debug_print("Unexpected in process_loop")

    finally:
        debug_print("Process loop finished")


def ensure_process_thread():
    """Ensure single background processing thread is running."""
    global process_thread
    with process_lock:
        if process_thread is None or not process_thread.is_alive():
            process_thread = threading.Thread(target=process_loop, daemon=True)
            process_thread.start()


def on_open(ws):
    """Raw stream mode: no SUBSCRIBE needed."""
    debug_print("WebSocket opened (raw stream)")


def on_message(ws, message):
    """WS message -> parse and route."""
    try:
        data = json.loads(message)
        if "k" in data.get("data", {}) or "k" in data:
            # Support both combined-style {data:{k:...}} and raw {k:...}
            kline = data["data"]["k"] if "data" in data else data["k"]
            symbol = data["data"]["s"] if "data" in data else data["s"]
            event_time_ms = (data["data"]["E"] if "data" in data else data["E"])

            process_kline_data(symbol, kline, event_time_ms)
    except json.JSONDecodeError as e:
        print(f"Ошибка декодирования JSON: {e}")
        debug_print("JSON decode error")
    except Exception as e:
        log_error("Ошибка обработки данных", e, "on_message")


def process_kline_data(symbol: str, k: Dict[str, Any], event_time_ms: int):
    """Transform kline into canonical candle and signal processing."""
    try:
        key = f"{symbol}_{SYSTEM_TIMEFRAME}"

        # Timestamps
        open_time_str = datetime.fromtimestamp(k["t"] / 1000, timezone.utc).strftime("%Y-%m-%d %H:%M:%S:000")
        close_time_str = datetime.fromtimestamp(k["T"] / 1000, timezone.utc).strftime("%Y-%m-%d %H:%M:%S:999")
        ts_str = datetime.fromtimestamp(event_time_ms / 1000, timezone.utc).strftime("%Y-%m-%d %H:%M:%S:%f")[:-3]

        with candles_lock:
            candles[key] = {
                "CLOSE_TIME": close_time_str,
                "TIMESTAMP": ts_str,
                "OPEN_TIME": open_time_str,
                "HIGH_PRICE": float(k["h"]),
                "CLOSE_PRICE": float(k["c"]),
                "OPEN_PRICE": float(k["o"]),
                "LOW_PRICE": float(k["l"]),
            }

        ensure_process_thread()
        process_event.set()

    except KeyError as e:
        print(f"Отсутствует ожидаемое поле в данных: {e}")
    except ValueError as e:
        print(f"Ошибка преобразования данных: {e}")
    except Exception as e:
        log_error("Ошибка обработки данных", e, "process_kline_data")


def on_error(ws, error):
    """WS error -> finalize. Respect Ctrl+C initiated shutdown."""
    if shutdown_event.is_set():
        # We are shutting down because of Ctrl+C or explicit stop
        finalize(stop_reason or USER_INTERRUPT_REASON, ws, shutdown_for_exit=True)
        return
    # Critical runtime error (not user-initiated) — close WS and allow reconnect
    finalize(f"WebSocket ошибка: {error}", ws, shutdown_for_exit=False)


def on_close(ws, close_status_code, close_msg):
    """WS close -> finalize with proper reason."""
    if FINALIZED.is_set():
        return
    if shutdown_event.is_set():
        finalize(stop_reason or USER_INTERRUPT_REASON, ws, shutdown_for_exit=True)
        return
    if close_status_code and close_status_code != 1000:
        finalize(f"WebSocket закрыт с ошибкой: {close_status_code}, сообщение: {close_msg}", ws, shutdown_for_exit=False)
    else:
        finalize("WebSocket закрыт нормально", ws, shutdown_for_exit=False)


def on_ping(wsapp, message):
    """Handle ping frame."""
    debug_print(f"PING received ({len(message)} bytes)")


def on_pong(wsapp, message):
    """Handle pong frame."""
    debug_print(f"PONG received ({len(message)} bytes)")


def signal_handler(sig, frame):
    """SIGINT handler: request shutdown, close WS, then raise KeyboardInterrupt."""
    global stop_reason, settings_monitor_active, restart_timer_active
    shutdown_event.set()
    stop_reason = USER_INTERRUPT_REASON

    settings_monitor_active = False
    restart_timer_active = False

    ws = current_ws
    if ws is not None:
        try:
            ws.keep_running = False
            ws.close()
        except Exception as e:
            log_error("WebSocket ошибка при закрытии", e)

    # Interrupt current flow immediately; will be caught and finalized
    raise KeyboardInterrupt


# =========================
# Background monitors
# =========================
def settings_monitor():
    """Watch settings every 5s; trigger immediate restart on changes."""
    global settings_monitor_active
    while settings_monitor_active and not shutdown_event.is_set():
        try:
            if shutdown_event.wait(5):
                break
            if not settings_monitor_active:
                break

            current_raw = load_settings()
            validated = validate_settings(current_raw)
            needs_restart, needs_file_clear = check_settings_changes(validated)

            if needs_restart:
                print("⚡ Немедленный перезапуск из-за изменения настроек")
                if needs_file_clear:
                    reset_candles(clear_file=True)
                # Planned restart: do not set shutdown_event, but wait for main scripts if running
                finalize("Перезапуск из-за изменения SYSTEM_TIMEFRAME или SYSTEM_SYMBOL", current_ws, shutdown_for_exit=False)
                break

        except KeyboardInterrupt:
            break
        except Exception as e:
            debug_print(f"Settings monitor error: {e}")
            if shutdown_event.wait(1):
                break


# =========================
# Main
# =========================
if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)

    # Initial scripts
    execute_scripts(BEFORE_SCRIPTS, "начальных скриптов")

    backoff = BACKOFF_BASE_SECONDS

    while True:
        try:
            FINALIZED.clear()
            shutdown_event.clear()

            # Load + validate settings
            settings_raw = load_settings()
            settings = validate_settings(settings_raw)
            needs_restart, needs_file_clear = check_settings_changes(settings)
            if needs_file_clear:
                reset_candles(clear_file=True)

            SYSTEM_TIMEFRAME = settings["SYSTEM_TIMEFRAME"]
            SYSTEM_SYMBOL = settings["SYSTEM_SYMBOL"]
            WEBSOCKET_RESTART_INTERVAL = settings["WEBSOCKET_RESTART_INTERVAL"]

            # Construct raw stream URL for exactly one pair
            stream_url = f"{WS_BASE_WS}/{SYSTEM_SYMBOL.lower()}@kline_{SYSTEM_TIMEFRAME}"
            debug_print(f"Using RAW stream URL: {stream_url}")

            if needs_restart:
                print("⚡ Принудительный перезапуск из-за изменения настроек")
                continue

            # WebSocket app (raw mode, no subscribe)
            websocket.enableTrace(False)
            ws = websocket.WebSocketApp(
                stream_url,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                on_ping=on_ping,
                on_pong=on_pong,
            )
            current_ws = ws

            # Start settings monitor
            settings_monitor_active = True
            monitor_thread = threading.Thread(target=settings_monitor, daemon=True)
            monitor_thread.start()

            # Restart timer thread (graceful periodic reconnect)
            def restart_timer():
                global settings_monitor_active, restart_timer_active
                total = WEBSOCKET_RESTART_INTERVAL * 60
                for _ in range(total):
                    if not restart_timer_active or shutdown_event.is_set():
                        debug_print("Restart timer stopped")
                        return
                    time.sleep(1)
                settings_monitor_active = False
                restart_timer_active = False
                # Planned restart by interval
                finalize(f"Перезапуск по таймеру ({WEBSOCKET_RESTART_INTERVAL} минут)", ws, shutdown_for_exit=False)
                debug_print("Restart timer triggered")

            restart_timer_active = True
            timer_thread = threading.Thread(target=restart_timer, daemon=True)
            timer_thread.start()

            debug_print("Starting WS run_forever with heartbeat")
            ws.run_forever(ping_interval=PING_INTERVAL, ping_timeout=PING_TIMEOUT)

            # Cleanup threads after WS exits
            settings_monitor_active = False
            restart_timer_active = False
            safe_join(monitor_thread, timeout=2)
            safe_join(timer_thread, timeout=2)

            # Stop main loop if shutdown was requested (Ctrl+C etc.)
            if shutdown_event.is_set():
                if not FINALIZED.is_set():
                    finalize(stop_reason or USER_INTERRUPT_REASON, ws, shutdown_for_exit=True)
                break

            # Reconnect policy with exponential backoff + jitter
            reason = LAST_FINALIZE_REASON or ""
            # Reset backoff on planned restarts
            if ("Перезапуск по таймеру" in reason) or ("изменения настроек" in reason) or ("SYSTEM_TIMEFRAME" in reason) or ("SYSTEM_SYMBOL" in reason) or ("WebSocket закрыт нормально" in reason):
                backoff = BACKOFF_BASE_SECONDS
            else:
                jitter = random.uniform(0, JITTER_MAX_MS / 1000.0)
                wait_s = min(backoff, BACKOFF_MAX_SECONDS) + jitter
                print(f"⏳ Пауза перед реконнектом: {wait_s:.2f} сек")
                responsive_sleep(wait_s)
                backoff = min(backoff * 2, BACKOFF_MAX_SECONDS)

        except KeyboardInterrupt:
            # Unified Ctrl+C path
            shutdown_event.set()
            settings_monitor_active = False
            restart_timer_active = False
            if not FINALIZED.is_set():
                finalize(stop_reason or USER_INTERRUPT_REASON, current_ws, shutdown_for_exit=True)
            break
        except Exception as e:
            # Missing settings file — exit
            if isinstance(e, FileNotFoundError):
                shutdown_event.set()
                if not FINALIZED.is_set():
                    finalize(f"Файл настроек {SETTINGS_PATH} не найден", current_ws, shutdown_for_exit=True)
                break

            # Generic hard error path -> brief pause then retry with backoff
            shutdown_event.set()
            settings_monitor_active = False
            restart_timer_active = False
            safe_join(monitor_thread, timeout=2)
            safe_join(timer_thread, timeout=2)
            show_last_execution_time()
            log_error("Критическая ошибка в главном цикле", e)
            debug_print("Critical error in main loop, restarting...")

            jitter = random.uniform(0, JITTER_MAX_MS / 1000.0)
            wait_s = min(backoff, BACKOFF_MAX_SECONDS) + jitter
            print(f"⏳ Пауза перед реконнектом: {wait_s:.2f} сек")
            try:
                responsive_sleep(wait_s)
            except KeyboardInterrupt:
                if not FINALIZED.is_set():
                    finalize(stop_reason or USER_INTERRUPT_REASON, current_ws, shutdown_for_exit=True)
                break
            backoff = min(backoff * 2, BACKOFF_MAX_SECONDS)
