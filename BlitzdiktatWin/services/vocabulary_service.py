# Copyright (c) 2026 Thorben Meier. MIT License.
"""
Persistentes Vokabular, das nach jeder Transkription automatisch erweitert wird.
Gespeichert in %APPDATA%/Blitzdiktat/vocabulary.json.
"""

import json
import os

MAX_TERMS = 150


def _vocab_path() -> str:
    base = os.environ.get("APPDATA", os.path.expanduser("~"))
    folder = os.path.join(base, "Blitzdiktat")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "vocabulary.json")


def get_learned_terms() -> list[str]:
    path = _vocab_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def add_terms(terms: list[str]) -> None:
    if not terms:
        return
    existing = get_learned_terms()
    seen = {t.lower() for t in existing}
    new_terms = [t for t in terms if t.strip() and t.lower() not in seen]
    if not new_terms:
        return
    merged = existing + new_terms
    if len(merged) > MAX_TERMS:
        merged = merged[-MAX_TERMS:]
    try:
        with open(_vocab_path(), "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def clear() -> None:
    try:
        with open(_vocab_path(), "w", encoding="utf-8") as f:
            json.dump([], f)
    except Exception:
        pass
