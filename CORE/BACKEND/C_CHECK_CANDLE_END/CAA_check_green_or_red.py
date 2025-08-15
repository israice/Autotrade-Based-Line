import csv
import yaml
from pathlib import Path
import io
import contextlib
import operator

# ============================================================================
# НАСТРОЙКИ И КОНФИГУРАЦИЯ
# ============================================================================
YAML_PATH = Path("CORE/DATA/user_settings.yaml")
YAML_SYMBOL_KEY = "WEBSOCKET_SYMBOL"
YAML_TIMEFRAME_KEY = "WEBSOCKET_TIMEFRAME"
# ============================================================================
CSV_PATH = Path("CORE/DATA/Y_database.csv")
SYMBOL_COLUMN = "SYMBOL"
TIMEFRAME_COLUMN = "TIMEFRAME"
CANDLE_NUMBER_COLUMN = "CANDLE_NUMBER"
# ============================================================================
COMPARISON_COLUMN_1 = "OPEN_PRICE"  # Колонка для первого значения (CANDLE_NUMBER_1)
CANDLE_NUMBER_1 = "1"
COMPARISON_OPERATOR = '>'  # Поддерживаемые операторы: '==', '!=', '>', '<', '>=', '<='
CANDLE_NUMBER_2 = "2"
COMPARISON_COLUMN_2 = "OPEN_PRICE"  # Колонка для второго значения (CANDLE_NUMBER_2)
# ============================================================================

# SCRIPTS для разных результатов сравнения
SCRIPTS_TRUE = [
    "CORE/TOOLS_FLOW/message_END_GREEN.py",
    # "TOOLS/reset_COUNTER_HIGH_CROSSING.py",
    # "TOOLS/reset_COUNTER_OPEN_CROSSING.py",
    # "TOOLS/reset_COUNTER_LOW_CROSSING.py",
    # "TOOLS/reset_PERCENT_SELL.py",
    # "TOOLS/reset_TREND_STATUS.py",
    # "TOOLS/enable_CROSSING_UP_GREEN.py",
    # "TOOLS/disable_CROSSING_DOWN_GREEN.py",
    # "TOOLS/disable_CROSSING_UP_RED.py",
    # "TOOLS/enable_CROSSING_DOWN_RED.py",
]

SCRIPTS_FALSE = [
    "CORE/TOOLS_FLOW/message_END_RED.py",
    # "TOOLS/reset_COUNTER_HIGH_CROSSING.py",
    # "TOOLS/reset_COUNTER_OPEN_CROSSING.py",
    # "TOOLS/reset_COUNTER_LOW_CROSSING.py",
    # "TOOLS/reset_PERCENT_SELL.py",
    # "TOOLS/reset_TREND_STATUS.py",
    # "TOOLS/enable_CROSSING_UP_GREEN.py",
    # "TOOLS/disable_CROSSING_DOWN_GREEN.py",
    # "TOOLS/disable_CROSSING_UP_RED.py",
    # "TOOLS/enable_CROSSING_DOWN_RED.py",
]

# Messages
MESSAGE_COMPARISON_RESULT = "— {column1}({value1}) {operator} {column2}({value2}) = {result}"
MESSAGE_SCRIPT_NOT_FOUND = "Script not found: {}"
MESSAGE_SCRIPT_ERROR = "Error in {}: {}"
MESSAGE_MISSING_CANDLES = "Missing CANDLE_NUMBER 1 or 2 for given symbol/timeframe."
MESSAGE_INVALID_OPERATOR = "Invalid comparison operator: {}. Supported: ==, !=, >, <, >=, <="

# Словарь операторов
OPERATORS = {
    '==': operator.eq,
    '!=': operator.ne,
    '>': operator.gt,
    '<': operator.lt,
    '>=': operator.ge,
    '<=': operator.le
}

# ============================================================================
# ОСНОВНОЙ КОД
# ============================================================================

def load_settings(yaml_path):
    """Load settings from YAML file."""
    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_csv_data(csv_path):
    """Load CSV data into a list of dictionaries."""
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def compare_values(data, symbol, timeframe):
    """Compare values between CANDLE_NUMBER 1 and 2 for given symbol and timeframe."""
    if COMPARISON_OPERATOR not in OPERATORS:
        raise ValueError(MESSAGE_INVALID_OPERATOR.format(COMPARISON_OPERATOR))
    
    filtered = [row for row in data if row[SYMBOL_COLUMN] == symbol and row[TIMEFRAME_COLUMN] == timeframe]

    candle1 = next((row for row in filtered if row[CANDLE_NUMBER_COLUMN] == CANDLE_NUMBER_1), None)
    candle2 = next((row for row in filtered if row[CANDLE_NUMBER_COLUMN] == CANDLE_NUMBER_2), None)

    if not candle1 or not candle2:
        raise ValueError(MESSAGE_MISSING_CANDLES)

    try:
        value1 = float(candle1[COMPARISON_COLUMN_1])
        value2 = float(candle2[COMPARISON_COLUMN_2])
    except (ValueError, KeyError) as e:
        raise ValueError(f"Error converting values to float or column not found: {e}")

    # Выполняем сравнение
    comparison_func = OPERATORS[COMPARISON_OPERATOR]
    result = comparison_func(value1, value2)
    
    # Возвращаем результат сравнения и информацию для отладки
    comparison_info = {
        'result': result,
        'value1': value1,
        'value2': value2,
        'column1': COMPARISON_COLUMN_1,
        'column2': COMPARISON_COLUMN_2,
        'operator': COMPARISON_OPERATOR
    }
    
    return comparison_info


def run_scripts_exec(scripts):
    """Run Python scripts with exec() and capture their stdout without empty lines."""
    collected_output = []

    for script in scripts:
        script_path = Path(script)
        if not script_path.exists():
            collected_output.append(MESSAGE_SCRIPT_NOT_FOUND.format(script))
            continue

        with open(script_path, "r", encoding="utf-8") as f:
            code = f.read()

        output_buffer = io.StringIO()
        with contextlib.redirect_stdout(output_buffer):
            try:
                exec(code, {})
            except Exception as e:
                collected_output.append(MESSAGE_SCRIPT_ERROR.format(script, e))

        # Filter out empty lines
        output_lines = [line for line in output_buffer.getvalue().splitlines() if line.strip()]
        if output_lines:
            collected_output.extend(output_lines)

    return collected_output


def main():
    try:
        settings = load_settings(YAML_PATH)
        data = load_csv_data(CSV_PATH)

        for symbol in settings.get(YAML_SYMBOL_KEY, []):
            try:
                comparison_info = compare_values(data, symbol, settings[YAML_TIMEFRAME_KEY])
                
                # Определяем какие скрипты запускать
                if comparison_info['result']:
                    scripts_to_run = SCRIPTS_TRUE
                else:
                    scripts_to_run = SCRIPTS_FALSE
                
                # Запускаем скрипты если они есть
                if scripts_to_run:
                    symbol_output = run_scripts_exec(scripts_to_run)
                    if symbol_output:  # Print only if there is actual content
                        for line in symbol_output:
                            print(line)
                
                # Выводим информацию о сравнении для отладки
                message = MESSAGE_COMPARISON_RESULT.format(
                    column1=comparison_info['column1'],
                    value1=comparison_info['value1'],
                    operator=comparison_info['operator'],
                    column2=comparison_info['column2'],
                    value2=comparison_info['value2'],
                    result=comparison_info['result']
                )
                # print(f"{symbol} {message}")
                
            except ValueError as e:
                print(f"{symbol} Error: {e}")
                
    except Exception as e:
        print(f"Fatal error: {e}")


if __name__ == "__main__":
    main()