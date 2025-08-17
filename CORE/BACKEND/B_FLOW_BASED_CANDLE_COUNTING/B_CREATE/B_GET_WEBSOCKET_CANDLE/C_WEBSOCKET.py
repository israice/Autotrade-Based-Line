import websocket
import json
import yaml
import sys
import signal
from datetime import datetime, timezone
import threading
import time
import contextlib
import io
from typing import Dict, Any
import os

# Settings
WS_URL = "wss://fstream.binance.com/stream"
FILE_PATH = "CORE/DATA/AA_CANDLE.yaml"

BEFORE_SCRIPTS = [
    "CORE/BACKEND/A_BEFORE_START/A_RUN.py",
]

THE_MAIN_SCRIPTS = [
    "CORE/TOOLS_FLOW/DELAY_BY_SETTINGS.py",
    # #############################################
    "CORE/BACKEND/B_CREATE_PERCENT_DATA/B_RUN.py",
    "CORE/BACKEND/C_CHECK_CANDLE_END/C_RUN.py",
    "CORE/BACKEND/D_CHECK_PERCENT_SELL/D_RUN.py",
    "CORE/BACKEND/E_CHECK_OPEN_LINE_CROSS/E_RUN.py",
    # #############################################
    "CORE/BACKEND/Z_CHECK_END/Z_RUN.py",
]

last_execution_start_time = None

stop_reason = None
process_thread = None

previous_settings = {
    'WEBSOCKET_TIMEFRAME': None,
    'WEBSOCKET_SYMBOL': None,
    'symbol_count': 0
}

class RealTimeCapture:
    """Класс для захвата и отображения вывода в реальном времени"""
    def __init__(self, script_name: str, original_stdout):
        self.script_name = script_name
        self.original_stdout = original_stdout
    
    def write(self, text):
        """Перехватываем вывод и сразу отображаем без префикса"""
        if text and text.strip():  # убираем пустые строки
            lines = text.splitlines(keepends=True)
            for line in lines:
                if line.strip():  # Игнорируем пустые строки
                    self.original_stdout.write(line.rstrip() + '\n')
                    self.original_stdout.flush()
        return len(text)
    
    def flush(self):
        """Заглушка для совместимости"""
        self.original_stdout.flush()


# Глобальные переменные
candles: Dict[str, Dict[str, Any]] = {}
interrupted = False
processing = False
needs_process = False
candles_lock = threading.Lock()
settings_monitor_active = False
restart_timer_active = False  # добавлен флаг для координации таймеров
current_ws = None
monitor_thread = None
timer_thread = None
shutdown_event = threading.Event()  # событие для graceful shutdown

# Флаг для включения/выключения debug сообщений
DEBUG_MODE = False  # Установите в True для включения debug сообщений

def debug_print(message: str):
    """Удаляемые debug сообщения"""
    if DEBUG_MODE:
        print(f"DEBUG: {message}")

def clear_candles_file():
    """Очистка файла свечей при изменении настроек"""
    try:
        if os.path.exists(FILE_PATH):
            with open(FILE_PATH, 'w') as f:
                yaml.dump({}, f, sort_keys=False)
            print("🧹 Файл свечей очищен из-за изменения настроек")
            debug_print("Candles file cleared due to settings change")
    except Exception as e:
        handle_file_error(e, f"очистки файла {FILE_PATH}")

def check_settings_changes(current_settings):
    """Проверка изменений в критических настройках"""
    global previous_settings
    
    current_timeframe = current_settings['WEBSOCKET_TIMEFRAME']
    current_symbols = current_settings['WEBSOCKET_SYMBOL']
    current_symbol_count = len(current_symbols)
    
    # Проверяем изменения
    timeframe_changed = (previous_settings['WEBSOCKET_TIMEFRAME'] is not None and 
                        previous_settings['WEBSOCKET_TIMEFRAME'] != current_timeframe)
    
    symbols_changed = (previous_settings['WEBSOCKET_SYMBOL'] is not None and 
                      previous_settings['WEBSOCKET_SYMBOL'] != current_symbols)
    
    symbol_count_changed = (previous_settings['symbol_count'] != 0 and 
                           previous_settings['symbol_count'] != current_symbol_count)
    
    # Если что-то изменилось, нужен перезапуск
    needs_restart = timeframe_changed or symbols_changed
    needs_file_clear = symbol_count_changed or timeframe_changed or symbols_changed
    
    if timeframe_changed:
        print(f"🔄 Изменен таймфрейм: {previous_settings['WEBSOCKET_TIMEFRAME']} → {current_timeframe}")
    
    if symbols_changed:
        print(f"🔄 Изменены символы: {previous_settings['WEBSOCKET_SYMBOL']} → {current_symbols}")
    
    if symbol_count_changed:
        print(f"🔄 Изменено количество символов: {previous_settings['symbol_count']} → {current_symbol_count}")
    
    # Обновляем предыдущие настройки
    previous_settings['WEBSOCKET_TIMEFRAME'] = current_timeframe
    previous_settings['WEBSOCKET_SYMBOL'] = current_symbols.copy()
    previous_settings['symbol_count'] = current_symbol_count
    
    return needs_restart, needs_file_clear

def handle_file_error(error: Exception, operation: str):
    """Обработчик ошибок файловых операций"""
    error_msg = f"Ошибка {operation}: {str(error)}"
    print(error_msg)
    debug_print(f"File operation failed: {operation}")

def handle_websocket_error(error: Exception, context: str):
    """Обработчик ошибок WebSocket"""
    if isinstance(error, KeyboardInterrupt):
        return  # убираем сообщение о прерывании
    
    error_msg = f"WebSocket ошибка в {context}: {str(error)}"
    print(error_msg)
    debug_print(f"WebSocket error in {context}: {type(error).__name__}")

def handle_data_processing_error(error: Exception, data: Dict[str, Any]):
    """Обработчик ошибок обработки данных"""
    error_msg = f"Ошибка обработки данных: {str(error)}"
    print(error_msg)
    debug_print(f"Data processing error for: {data.get('s', 'unknown symbol')}")

def handle_script_execution_error(error: Exception, script: str):
    """Обработчик ошибок выполнения скриптов"""
    error_msg = f"Ошибка выполнения скрипта {script}: {str(error)}"
    print(error_msg)
    debug_print(f"Script execution failed: {script}")

def execute_scripts(scripts_list: list, description: str):
    """Выполнение списка скриптов напрямую через exec() с выводом в реальном времени"""
    global last_execution_start_time
    
    total_start_time = time.time()
    
    if description == "основных скриптов":
        last_execution_start_time = total_start_time
    
    for script in scripts_list:
        try:
            debug_print(f"Executing script: {script}")
            
            # Чтение файла скрипта
            try:
                with open(script, 'r', encoding='utf-8') as f:
                    script_code = f.read()
            except FileNotFoundError:
                print(f"Скрипт {script} не найден")
                continue
            except Exception as e:
                print(f"Ошибка чтения скрипта {script}: {str(e)}")
                continue
            
            # Создание контекста для выполнения
            script_name = script.split('/')[-1] if '/' in script else script.split('\\')[-1]
            script_globals = {
                '__name__': '__main__',
                '__file__': script,
            }
            
            # Сохраняем оригинальные потоки
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            
            # Создаем объекты для захвата вывода в реальном времени
            stdout_capture = RealTimeCapture(script_name, old_stdout)
            stderr_capture = RealTimeCapture(f"{script_name}[ERROR]", old_stderr)
            
            script_start_time = time.time()
            
            try:
                # Перенаправляем вывод и выполняем скрипт
                sys.stdout = stdout_capture
                sys.stderr = stderr_capture
                
                exec(script_code, script_globals)
                
            except Exception as e:
                # Используем оригинальный stderr для вывода ошибки
                old_stderr.write(f"[{script_name}[ERROR]] Ошибка выполнения: {str(e)}")
                old_stderr.flush()
                
            finally:
                # Восстанавливаем стандартные потоки
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                
                
        except Exception as e:
            handle_script_execution_error(e, script)
    
    total_end_time = time.time()
    total_execution_time = total_end_time - total_start_time
    
    if description == "основных скриптов":
        print(f"⚡ - {total_execution_time:.3f} СЕКУНД")
        last_execution_start_time = None

def process_loop():
    """Основной цикл обработки данных"""
    global needs_process, processing
    
    debug_print("Starting process loop")
    
    while needs_process:
        needs_process = False
        
        try:
            # Копирование данных свечей
            with candles_lock:
                current_candles = {k: v.copy() for k, v in candles.items()}
            
            debug_print(f"Processing {len(current_candles)} candles")
            
            # Сохранение в файл
            try:
                with open(FILE_PATH, 'w') as f:
                    yaml.dump(current_candles, f, sort_keys=False)
                debug_print(f"Data saved to {FILE_PATH}")
            except Exception as e:
                handle_file_error(e, f"сохранения данных в {FILE_PATH}")
                continue
            
            # Выполнение скриптов
            execute_scripts(THE_MAIN_SCRIPTS, "основных скриптов")
                    
        except Exception as e:
            print(f"Неожиданная ошибка в process_loop: {str(e)}")
            debug_print("Unexpected error in process_loop")

    processing = False
    debug_print("Process loop finished")

def on_open(ws):
    """Обработчик открытия WebSocket соединения"""
    try:
        subscribe_message = {
            "method": "SUBSCRIBE",
            "params": SUBSCRIBE_PARAMS,
            "id": 1
        }
        ws.send(json.dumps(subscribe_message))
        debug_print("WebSocket connection opened and subscribed")
    except Exception as e:
        handle_websocket_error(e, "on_open")

def on_message(ws, message):
    """Обработчик входящих сообщений"""
    try:
        data = json.loads(message)
        debug_print(f"Received message for symbol: {data.get('data', {}).get('s', 'unknown')}")
        
        if 'data' in data and 'k' in data['data']:
            process_kline_data(data)
        
    except json.JSONDecodeError as e:
        print(f"Ошибка декодирования JSON: {str(e)}")
        debug_print("JSON decode error in message")
    except Exception as e:
        handle_data_processing_error(e, data if 'data' in locals() else {})

def process_kline_data(data: Dict[str, Any]):
    """Обработка данных свечей"""
    try:
        k = data['data']['k']
        symbol = data['data']['s']
        key = f"{symbol}_{WEBSOCKET_TIMEFRAME}"
        
        # Преобразование временных меток
        open_time_str = datetime.fromtimestamp(
            k['t']/1000, timezone.utc
        ).strftime('%Y-%m-%d %H:%M:%S:000')
        
        close_time_str = datetime.fromtimestamp(
            k['T']/1000, timezone.utc
        ).strftime('%Y-%m-%d %H:%M:%S:999')
        
        timestamp_str = datetime.fromtimestamp(
            data['data']['E']/1000, timezone.utc
        ).strftime('%Y-%m-%d %H:%M:%S:%f')[:-3]
        
        # Обновление данных свечей
        with candles_lock:
            candles[key] = {
                'CLOSE_TIME': close_time_str,
                'TIMESTAMP': timestamp_str,
                'OPEN_TIME': open_time_str,
                'HIGH_PRICE': float(k['h']),
                'CLOSE_PRICE': float(k['c']),
                'OPEN_PRICE': float(k['o']),
                'LOW_PRICE': float(k['l'])
            }
        
        debug_print(f"Updated candle data for {key}")
        
        # Запуск обработки
        global needs_process, processing, process_thread
        needs_process = True
        if not processing:
            processing = True
            process_thread = threading.Thread(target=process_loop)
            process_thread.start()
            
    except KeyError as e:
        print(f"Отсутствует ожидаемое поле в данных: {str(e)}")
        debug_print("Missing expected field in kline data")
    except ValueError as e:
        print(f"Ошибка преобразования данных: {str(e)}")
        debug_print("Data conversion error in kline processing")
    except Exception as e:
        handle_data_processing_error(e, data)

def on_error(ws, error):
    """Обработчик ошибок WebSocket"""
    global stop_reason, process_thread
    if stop_reason is f"Остоновленно пользователем (Ctrl+C)":
        stop_reason = f"WebSocket ошибка: {str(error)}"
    ws.close()
    ws.keep_running = False
    if processing:
        if process_thread:
            process_thread.join()
    else:
        show_last_execution_time()
    if stop_reason:
        print(stop_reason)
        stop_reason = None
    handle_websocket_error(error, "WebSocket connection")

def on_close(ws, close_status_code, close_msg):
    """Обработчик закрытия WebSocket соединения"""
    global stop_reason
    if stop_reason is None and close_status_code and close_status_code != 1000:  # 1000 = нормальное закрытие
        stop_reason = f"WebSocket закрыт с ошибкой: {close_status_code}, сообщение: {close_msg}"
        if processing:
            if process_thread:
                process_thread.join()
        else:
            show_last_execution_time()
        print(stop_reason)
        stop_reason = None
    debug_print("WebSocket connection closed")

def signal_handler(sig, frame):
    """Обработчик сигнала прерывания"""
    global interrupted, stop_reason, process_thread, restart_timer_active, settings_monitor_active
    stop_reason = "🔧  Остановлено пользователем (Ctrl+C)"
    
    # Сигнализируем всем потокам о завершении
    shutdown_event.set()
    settings_monitor_active = False
    restart_timer_active = False
    
    if 'ws' in globals():
        ws.close()
        ws.keep_running = False
    if processing:
        print(stop_reason)
        stop_reason = None
        if process_thread:
            process_thread.join()
    else:
        show_last_execution_time()
        print(stop_reason)
        stop_reason = None
    interrupted = True

def show_last_execution_time():
    """Показать время выполнения последней итерации THE_MAIN_SCRIPTS"""
    global last_execution_start_time
    if last_execution_start_time is not None:
        current_time = time.time()
        execution_time = current_time - last_execution_start_time
        print(f"🔧  - {execution_time:.3f} СЕКУНД ")

def load_settings():
    """Загрузка настроек из файла"""
    try:
        with open('CORE/DATA/BB_USER_SETTINGS.yaml', 'r') as f:
            settings = yaml.safe_load(f)
        debug_print("Settings loaded successfully")
        return settings
    except FileNotFoundError:
        error_msg = "Файл настроек CORE/DATA/BB_USER_SETTINGS.yaml не найден"
        print(error_msg)
        raise
    except yaml.YAMLError as e:
        handle_file_error(e, "чтения настроек из YAML")
        raise
    except Exception as e:
        handle_file_error(e, "загрузки настроек")
        raise

def settings_monitor():
    """Мониторинг изменений настроек каждые 5 секунд"""
    global settings_monitor_active, current_ws, stop_reason, process_thread, restart_timer_active
    
    while settings_monitor_active and not shutdown_event.is_set():
        try:
            if shutdown_event.wait(5):  # Ждем 5 секунд или до сигнала завершения
                break
                
            if not settings_monitor_active:
                break
                
            # Загружаем текущие настройки
            current_settings = load_settings()
            needs_restart, needs_file_clear = check_settings_changes(current_settings)
            
            if needs_restart:
                print("⚡ Немедленный перезапуск из-за изменения настроек")
                stop_reason = "Перезапуск из-за изменения WEBSOCKET_TIMEFRAME или WEBSOCKET_SYMBOL"
                
                restart_timer_active = False
                settings_monitor_active = False
                
                if needs_file_clear:
                    clear_candles_file()
                    # Очищаем также данные в памяти
                    with candles_lock:
                        candles.clear()
                
                # Закрываем текущее соединение
                if current_ws:
                    current_ws.close()
                    current_ws.keep_running = False
                
                if processing and process_thread:
                    process_thread.join()
                else:
                    show_last_execution_time()
                
                print(stop_reason)
                stop_reason = None
                break
                
        except Exception as e:
            debug_print(f"Error in settings monitor: {str(e)}")
            if not shutdown_event.wait(1):  # Короткая пауза при ошибке
                continue

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    
    debug_print("Starting main loop")
    
    # Выполнение начальных скриптов при запуске
    execute_scripts(BEFORE_SCRIPTS, "начальных скриптов")
    
    while True:
        try:
            shutdown_event.clear()
            
            # Загрузка настроек
            settings = load_settings()
            
            needs_restart, needs_file_clear = check_settings_changes(settings)
            
            if needs_file_clear:
                clear_candles_file()
                # Очищаем также данные в памяти
                with candles_lock:
                    candles.clear()
            
            WEBSOCKET_TIMEFRAME = settings['WEBSOCKET_TIMEFRAME']
            WEBSOCKET_SYMBOL = settings['WEBSOCKET_SYMBOL']
            WEBSOCKET_RESTART_INTERVAL = settings['WEBSOCKET_RESTART_INTERVAL']
            SUBSCRIBE_PARAMS = [
                f"{symbol.lower()}@kline_{WEBSOCKET_TIMEFRAME}" 
                for symbol in WEBSOCKET_SYMBOL
            ]
            
            debug_print(f"Loaded settings: {len(WEBSOCKET_SYMBOL)} symbols, {WEBSOCKET_TIMEFRAME} timeframe")
            
            if needs_restart:
                print("⚡ Принудительный перезапуск из-за изменения настроек")
                # Пропускаем создание WebSocket и переходим к следующей итерации
                continue
            
            # Настройка WebSocket
            websocket.enableTrace(False)
            ws = websocket.WebSocketApp(
                WS_URL,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )
            
            current_ws = ws
            
            settings_monitor_active = True
            monitor_thread = threading.Thread(target=settings_monitor)
            monitor_thread.start()
            
            # Таймер перезапуска
            def restart_timer():
                global stop_reason, process_thread, settings_monitor_active, restart_timer_active
                
                for i in range(WEBSOCKET_RESTART_INTERVAL * 60):
                    if not restart_timer_active or shutdown_event.is_set():
                        debug_print("Restart timer stopped")
                        return
                    time.sleep(1)
                
                settings_monitor_active = False
                restart_timer_active = False
                
                stop_reason = f"Перезапуск по таймеру ({WEBSOCKET_RESTART_INTERVAL} минут)"
                if 'ws' in globals():
                    ws.close()
                    ws.keep_running = False
                if processing:
                    if process_thread:
                        process_thread.join()
                else:
                    show_last_execution_time()
                print(stop_reason)
                stop_reason = None
                debug_print("Restart timer triggered")

            restart_timer_active = True
            timer_thread = threading.Thread(target=restart_timer)
            timer_thread.start()
            
            debug_print("Starting WebSocket connection")
            ws.run_forever()
            
            settings_monitor_active = False
            restart_timer_active = False

            if monitor_thread and monitor_thread.is_alive():
                monitor_thread.join(timeout=2)
            if timer_thread and timer_thread.is_alive():
                timer_thread.join(timeout=2)

            if interrupted:
                break
                
        except KeyboardInterrupt:
            shutdown_event.set()
            settings_monitor_active = False
            restart_timer_active = False
            
            # Ждем завершения потоков
            if monitor_thread and monitor_thread.is_alive():
                monitor_thread.join(timeout=2)
            if timer_thread and timer_thread.is_alive():
                timer_thread.join(timeout=2)
                
            if stop_reason is None:
                stop_reason = "Остановлено пользователем (KeyboardInterrupt)"
                show_last_execution_time()
                print(stop_reason)
            break
        except Exception as e:
            shutdown_event.set()
            settings_monitor_active = False
            restart_timer_active = False
            
            # Ждем завершения потоков
            if monitor_thread and monitor_thread.is_alive():
                monitor_thread.join(timeout=2)
            if timer_thread and timer_thread.is_alive():
                timer_thread.join(timeout=2)
                
            stop_reason = f"Критическая ошибка в главном цикле: {str(e)}"
            show_last_execution_time()
            print(stop_reason)
            debug_print("Critical error in main loop, restarting...")
            time.sleep(2)  # Пауза перед перезапуском