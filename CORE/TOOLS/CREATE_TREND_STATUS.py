#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import sys
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq

DEFAULT_PATH = Path("CORE") / "DATA" / "CC_TRIGGERS_CONFIG.yaml"

def to_float(value: Any):
    """Преобразует значение к float, если возможно, иначе возвращает None."""
    try:
        return float(value)
    except Exception:
        return None

def update_in_map(m: CommentedMap) -> bool:
    """
    Ищет PERCENT_STATUS в этой мапе и, если надо, обновляет/вставляет TREND_STATUS.
    Возвращает True, если были изменения.
    """
    changed = False
    if "PERCENT_STATUS" in m:
        f = to_float(m["PERCENT_STATUS"])
        if f is not None:
            if f > 0:
                trend = "GREEN"
            elif f < 0:
                trend = "RED"
            else:
                trend = None  # 0: ничего не делаем

            if trend is not None:
                if "TREND_STATUS" in m:
                    if m["TREND_STATUS"] != trend:
                        m["TREND_STATUS"] = trend
                        changed = True
                else:
                    # Вставляем сразу ПОСЛЕ PERCENT_STATUS, сохраняя порядок
                    keys = list(m.keys())
                    idx = keys.index("PERCENT_STATUS")
                    m.insert(idx + 1, "TREND_STATUS", trend)
                    changed = True
    return changed

def walk(node: Any) -> bool:
    """
    Рекурсивно обходит структуру (мапы и списки), обновляя все вхождения.
    Возвращает True, если были изменения.
    """
    changed = False
    if isinstance(node, CommentedMap):
        if update_in_map(node):
            changed = True
        # Продолжаем обход по значениям этой мапы
        for v in node.values():
            if walk(v):
                changed = True
    elif isinstance(node, (list, CommentedSeq, tuple)):
        for item in node:
            if walk(item):
                changed = True
    return changed

def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PATH
    if not path.exists():
        print(f"Файл не найден: {path}", file=sys.stderr)
        sys.exit(1)

    yaml = YAML(typ="rt")  # round-trip: сохраняет формат/комментарии/порядок
    yaml.preserve_quotes = True

    with path.open("r", encoding="utf-8") as f:
        docs = list(yaml.load_all(f))

    if not docs:
        print("YAML пустой — изменений нет.")
        return

    changed_any = False
    for i, doc in enumerate(docs):
        if walk(doc):
            changed_any = True
            docs[i] = doc

    if changed_any:
        # Перезаписываем файл с сохранением структуры
        with path.open("w", encoding="utf-8") as f:
            yaml.dump_all(docs, f)

if __name__ == "__main__":
    main()
