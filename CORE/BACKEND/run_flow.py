import yaml
import os
import sys
import builtins

# =========================
# Settings (configurable)
# =========================
CONFIG_PATH = 'settings.yaml'
CONFIG_HEADER = 'SYSTEM_RUN'

# Используем ТОЛЬКО эти два:
SCRIPTS_UP_WORD = 'ENABLE'
SCRIPTS_YES = [
    "CORE/BACKEND/C_THE_FLOW/A_RUN.py",
]

# Поведение вывода
FORCE_FLUSH_PRINTS = True                   # Форсируем flush=True внутри дочерних скриптов
LINE_BUFFER_STDIO = True                    # Линейная буферизация stdout/stderr, если доступна

# =========================
# Helpers
# =========================
if LINE_BUFFER_STDIO:
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass
    try:
        sys.stderr.reconfigure(line_buffering=True)
    except Exception:
        pass

_original_print = builtins.print
def _print_flush(*args, **kwargs):
    kwargs.setdefault('flush', True)
    return _original_print(*args, **kwargs)

# =========================
# Logic
# =========================
config_value = None
config_loaded = False

try:
    with open(CONFIG_PATH, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file) or {}
        config_loaded = True
        if CONFIG_HEADER in config:
            config_value = config.get(CONFIG_HEADER)
        else:
            print(f"[INFO] В {CONFIG_PATH} не найден ключ '{CONFIG_HEADER}'. Скрипты не будут запущены.", flush=True)
except FileNotFoundError:
    print(f"[INFO] Файл конфигурации не найден: {CONFIG_PATH}. Скрипты не будут запущены.", flush=True)
except yaml.YAMLError as e:
    print(f"[ERROR] Ошибка разбора YAML в {CONFIG_PATH}: {e}. Скрипты не будут запущены.", flush=True)

# Если конфиг загружен и значение найдено — проверяем его
if config_loaded and config_value is not None:
    if str(config_value) != SCRIPTS_UP_WORD:
        print(
            f"[INFO] Значение '{CONFIG_HEADER}' = '{config_value}' (ожидалось '{SCRIPTS_UP_WORD}'). "
            "Скрипты не будут запущены.",
            flush=True
        )
        sys.exit(0)
    # Иначе: ENABLE — запускаем только SCRIPTS_YES
    scripts = SCRIPTS_YES
else:
    # Значение не найдено — уже напечатали сообщение выше, просто выходим
    sys.exit(0)

# Запуск скриптов из SCRIPTS_YES
for script in scripts:
    if not os.path.exists(script):
        print(f"[ERROR] Не найден скрипт: {script}", flush=True)
        continue

    try:
        with open(script, 'r', encoding='utf-8') as f:
            code = compile(f.read(), script, 'exec')

        exec_globals = {'__name__': '__main__', '__file__': script}

        if FORCE_FLUSH_PRINTS:
            builtins.print = _print_flush
        try:
            exec(code, exec_globals)
        finally:
            builtins.print = _original_print

    except Exception as e:
        print(f"[ERROR] Ошибка выполнения {script}: {e}", flush=True)
