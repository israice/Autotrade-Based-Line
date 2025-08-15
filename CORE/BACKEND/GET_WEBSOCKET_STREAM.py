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

# Settings
WS_URL = "wss://fstream.binance.com/stream"
FILE_PATH = "CORE/DATA/A_candle.yaml"

BEFORE_SCRIPTS = [
    "CORE/BACKEND/A_RUN_BEFORE_START/A_RUN.py",
]

THE_MAIN_SCRIPTS = [
    "CORE/TOOLS_FLOW/DELAY_BY_SETTINGS.py",
    # ##############################################
    "CORE/BACKEND/B_CHECK_CANDLE_END/B_RUN.py",
    # "CORE/BACKEND/B_CREATE_DATA/B_run.py",
    # "CORE/BACKEND/C_CHECK_CANDLE_END/C_if_candle_ends.py",
    # "CORE/BACKEND/D_CHECK_PERCENT_SELL/D_if_percent_positive_or_negative.py",
    # "CORE/BACKEND/E_CHECK_OPEN_LINE_CROSS/E_if_trend_changes.py",
    # "CORE/BACKEND/F_CHECK_HIGH_LOW_CROSS/F_if_candle_one_outside.py",
    # ##############################################
    "CORE/BACKEND/Z_UPDATE_ON_END/Z_RUN.py",
]

last_execution_start_time = None
stop_reason = None

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
main_scripts_executing = False
pending_stop = False

# Флаг для включения/выключения debug сообщений
DEBUG_MODE = False  # Установите в True для включения debug сообщений

def debug_print(message: str):
    """Удаляемые debug сообщения"""
    if DEBUG_MODE:
        print(f"DEBUG: {message}")

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
    global last_execution_start_time, main_scripts_executing
    
    total_start_time = time.time()
    
    if description == "основных скриптов":
        last_execution_start_time = total_start_time
        main_scripts_executing = True
    
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
        main_scripts_executing = False
        
        global pending_stop
        if pending_stop:
            handle_pending_stop()

def handle_pending_stop():
    """Обработка отложенной остановки после завершения THE_MAIN_SCRIPTS"""
    global stop_reason, interrupted
    if stop_reason:
        print(stop_reason)
    interrupted = True
    if 'ws' in globals():
        ws.close()

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
        global needs_process, processing
        needs_process = True
        if not processing:
            processing = True
            threading.Thread(target=process_loop, daemon=True).start()
            
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
    global stop_reason, main_scripts_executing, pending_stop
    stop_reason = f"WebSocket ошибка: {str(error)}"
    
    if main_scripts_executing:
        pending_stop = True
        debug_print("WebSocket error during THE_MAIN_SCRIPTS execution, waiting for completion...")
        return
    
    handle_websocket_error(error, "WebSocket connection")

def on_close(ws, close_status_code, close_msg):
    """Обработчик закрытия WebSocket соединения"""
    global stop_reason, main_scripts_executing, pending_stop
    if close_status_code and close_status_code != 1000:  # 1000 = нормальное закрытие
        stop_reason = f"WebSocket закрыт с ошибкой: {close_status_code}, сообщение: {close_msg}"
        
        if main_scripts_executing:
            pending_stop = True
            debug_print("WebSocket close during THE_MAIN_SCRIPTS execution, waiting for completion...")
            return
            
        print(stop_reason)
    debug_print("WebSocket connection closed")

def signal_handler(sig, frame):
    """Обработчик сигнала прерывания"""
    global interrupted, stop_reason, main_scripts_executing, pending_stop
    stop_reason = "🔧  Остановлено пользователем (Ctrl+C)"
    
    if main_scripts_executing:
        pending_stop = True
        debug_print("Stop signal received during THE_MAIN_SCRIPTS execution, waiting for completion...")
        return
    
    show_last_execution_time()
    print(stop_reason)
    debug_print("Interrupt signal received")
    ws.close()
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
        with open('CORE/DATA/user_settings.yaml', 'r') as f:
            settings = yaml.safe_load(f)
        debug_print("Settings loaded successfully")
        return settings
    except FileNotFoundError:
        error_msg = "Файл настроек CORE/DATA/user_settings.yaml не найден"
        print(error_msg)
        raise
    except yaml.YAMLError as e:
        handle_file_error(e, "чтения настроек из YAML")
        raise
    except Exception as e:
        handle_file_error(e, "загрузки настроек")
        raise

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    
    debug_print("Starting main loop")
    
    # Выполнение начальных скриптов при запуске
    execute_scripts(BEFORE_SCRIPTS, "начальных скриптов")
    
    while True:
        try:
            # Загрузка настроек
            settings = load_settings()
            
            WEBSOCKET_TIMEFRAME = settings['WEBSOCKET_TIMEFRAME']
            WEBSOCKET_SYMBOL = settings['WEBSOCKET_SYMBOL']
            WEBSOCKET_RESTART_INTERVAL = settings['WEBSOCKET_RESTART_INTERVAL']
            SUBSCRIBE_PARAMS = [
                f"{symbol.lower()}@kline_{WEBSOCKET_TIMEFRAME}" 
                for symbol in WEBSOCKET_SYMBOL
            ]
            
            debug_print(f"Loaded settings: {len(WEBSOCKET_SYMBOL)} symbols, {WEBSOCKET_TIMEFRAME} timeframe")
            
            # Настройка WebSocket
            websocket.enableTrace(False)
            ws = websocket.WebSocketApp(
                WS_URL,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )
            
            # Таймер перезапуска
            def restart_timer():
                global stop_reason, main_scripts_executing, pending_stop
                time.sleep(WEBSOCKET_RESTART_INTERVAL * 60)
                stop_reason = f"Перезапуск по таймеру ({WEBSOCKET_RESTART_INTERVAL} минут)"
                
                if main_scripts_executing:
                    pending_stop = True
                    debug_print("Restart timer triggered during THE_MAIN_SCRIPTS execution, waiting for completion...")
                    return
                
                show_last_execution_time()
                print(stop_reason)
                debug_print("Restart timer triggered")
                ws.close()

            timer = threading.Thread(target=restart_timer, daemon=True)
            timer.start()
            
            debug_print("Starting WebSocket connection")
            ws.run_forever()
            
            if interrupted:
                break
                
        except KeyboardInterrupt:
            if stop_reason is None:
                stop_reason = "Остановлено пользователем (KeyboardInterrupt)"
                show_last_execution_time()
                print(stop_reason)
            break
        except Exception as e:
            stop_reason = f"Критическая ошибка в главном цикле: {str(e)}"
            show_last_execution_time()
            print(stop_reason)
            debug_print("Critical error in main loop, restarting...")
            time.sleep(5)  # Пауза перед перезапуском
