import contextlib
import io
import sys
import traceback

# ################### #
# run list of scripts #
# ################### #

# Список скриптов для запуска
SCRIPTS = [
    "CORE/TOOLS_FLOW/ping.py",
]

def run_script(script_path):
    """Функция для безопасного запуска скрипта и захвата его вывода"""
    try:
        # Чтение кода скрипта
        with open(script_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Подготовка для захвата вывода
        output_capture = io.StringIO()
        
        # Сохранение текущего stdout и stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        
        try:
            # Перенаправление stdout и stderr
            with contextlib.redirect_stdout(output_capture), contextlib.redirect_stderr(output_capture):
                exec(code, {})  # Пустой словарь для изоляции пространства имен
            
            # Получение захваченного вывода
            captured_output = output_capture.getvalue()
            
            # Удаление пустых строк
            lines = [line for line in captured_output.splitlines() if line.strip()]
            filtered_output = '\n'.join(lines)
            
            # Вывод результатов только если есть непустой вывод
            if filtered_output:
                print(f"{filtered_output}")
                
        finally:
            # Восстановление stdout и stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            
    except FileNotFoundError:
        print(f"Error: Script {script_path} not found")
    except Exception as e:
        print(f"Error in {script_path}: {traceback.format_exc().strip()}")

# Запуск всех скриптов
for script_path in SCRIPTS:
    run_script(script_path)