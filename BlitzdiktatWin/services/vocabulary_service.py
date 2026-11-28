# Copyright (c) 2026 Thorben Meier. MIT License.
"""
Persistentes Vokabular – und dafür sorgen, dass es auch wirkt.

Gespeichert in %APPDATA%/Blitzdiktat:
  vocabulary.json              Liste der richtigen Schreibweisen (Namen, Fachbegriffe)
  vocabulary_corrections.json  bekannte Fehlschreibungen → richtige Schreibweise

Das Vokabular wirkt an zwei Stellen:

1. Als Hinweis an die Spracherkennung (siehe ``prompt_terms``). Das ist nur ein
   schwacher Hinweis – Whisper schreibt "Torben" trotzdem oft ohne h.
2. Als Korrektur NACH der Erkennung (``apply``). Erst sie macht das Vokabular
   verlässlich:
     a) bekannte Fehlschreibungen werden ersetzt ("Torben" → "Thorben"),
     b) großgeschriebene Wörter ab fünf Buchstaben, die sich von einem
        Vokabel-Begriff nur durch th/t, ph/f, y/i oder C/K am Anfang unterscheiden, werden
        auf die Schreibweise des Vokabulars gebracht (Tomas → Thomas, Meyer → Meier).
        Bewusst eng: Mit gröberen Regeln (Doppelbuchstaben, Dehnungs-h, ie/i,
        ai/ei, ß/ss) wurden normale Wörter verfälscht – "kann" zu "Kahn",
        "Miete" zu "Mitte", "mehr" zu "Meer". Für alles andere gibt es a).
     c) mehrteilige Begriffe werden vereinheitlicht ("Online KI" → "Online-KI").

Früher lernte die App nach jedem Diktat automatisch Begriffe dazu – auch falsch
erkannte. "Torben" stand dann neben dem korrigierten "Thorben" wieder in der
Liste. ``add_terms`` nimmt deshalb keine Varianten vorhandener Begriffe und
keine bekannten Fehlschreibungen mehr auf; speichert der Nutzer die Liste
(``save_user_list``), wird aus einer entfernten Variante eine Korrektur.
"""

import json
import os
import re

MAX_TERMS = 150
# Whisper liest höchstens rund 220 Tokens Hinweis; lange Listen würden vorn abgeschnitten.
PROMPT_MAX_TERMS = 60
PROMPT_MAX_CHARS = 500
_ARROW = re.compile(r"\s*(?:->|=>|→|⇒)\s*")
_WORD = re.compile(r"[^\W\d_]+")


def _folder() -> str:
    base = os.environ.get("APPDATA", os.path.expanduser("~"))
    folder = os.path.join(base, "Blitzdiktat")
    os.makedirs(folder, exist_ok=True)
    return folder


def _vocab_path() -> str:
    return os.path.join(_folder(), "vocabulary.json")


def _corrections_path() -> str:
    return os.path.join(_folder(), "vocabulary_corrections.json")


# ── Lesen und Schreiben ─────────────────────────────────────────────────────

def get_learned_terms() -> list[str]:
    try:
        with open(_vocab_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
        return [t for t in data if isinstance(t, str) and t.strip()] if isinstance(data, list) else []
    except Exception:
        return []


def get_corrections() -> dict[str, str]:
    """Fehlschreibung (klein geschrieben) → richtige Schreibweise."""
    try:
        with open(_corrections_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {}
        return {str(k).lower(): str(v) for k, v in data.items() if str(k).strip() and str(v).strip()}
    except Exception:
        return {}


def _write(path: str, data) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def clear() -> None:
    _write(_vocab_path(), [])
    _write(_corrections_path(), {})


# ── Schreibweisen vergleichen ───────────────────────────────────────────────

# Nur Unterschiede, die praktisch nie zwei verschiedene deutsche Wörter trennen.
_ORTHO_RULES = [("ph", "f"), ("th", "t"), ("y", "i")]
# c/k nur am Wortanfang (Carstens/Karstens, Carl/Karl). Mitten im Wort trennt es deutsche von
# englischen Wörtern: "Projekt" würde sonst zu "Project", "Lokal" zu "Local".
_C_NOT_CH = re.compile(r"^c(?![hk])")
FUZZY_MIN_LEN = 5


def ortho_key(word: str) -> str:
    """Gleicher Schlüssel = gleiches Wort in anderer Schreibweise (Thorben/Torben, Meier/Meyer)."""
    w = word.lower()
    for old, new in _ORTHO_RULES:
        w = w.replace(old, new)
    return _C_NOT_CH.sub("k", w)


def _fuzzy_ok(word: str) -> bool:
    """Nur Namen und Begriffe: großgeschrieben und lang genug (nicht "Tor" → "Thor")."""
    return len(word) >= FUZZY_MIN_LEN and word[:1].isupper()


def is_variant(a: str, b: str) -> bool:
    """Zwei einzelne Wörter, die sich nur in der Schreibweise unterscheiden."""
    a, b = a.strip(), b.strip()
    if not a or not b or a.lower() == b.lower() or not _single_word(a) or not _single_word(b):
        return False
    return ortho_key(a) == ortho_key(b)


def _single_word(term: str) -> bool:
    return bool(_WORD.fullmatch(term))


# ── Lernen ──────────────────────────────────────────────────────────────────

def add_terms(terms: list[str]) -> None:
    """Nimmt automatisch gelernte Begriffe auf – aber keine Fehlschreibungen und
    keine anderen Schreibweisen von Begriffen, die schon im Vokabular stehen."""
    if not terms:
        return
    existing = get_learned_terms()
    corrections = get_corrections()
    seen = {t.lower() for t in existing}
    keys = {ortho_key(t) for t in existing if _single_word(t)}
    new_terms: list[str] = []
    for term in terms:
        term = (term or "").strip()
        low = term.lower()
        if not term or low in seen or low in corrections:
            continue
        if _single_word(term) and ortho_key(term) in keys:
            continue                                    # Variante eines vorhandenen Begriffs
        seen.add(low)
        if _single_word(term):
            keys.add(ortho_key(term))
        new_terms.append(term)
    if not new_terms:
        return
    merged = existing + new_terms
    if len(merged) > MAX_TERMS:
        merged = merged[-MAX_TERMS:]
    _write(_vocab_path(), merged)


def parse_user_lines(lines: list[str]) -> tuple[list[str], dict[str, str]]:
    """Zeilen der Vokabelliste: "Begriff" oder "falsch -> richtig"."""
    terms: list[str] = []
    corrections: dict[str, str] = {}
    seen: set[str] = set()

    def add(term: str) -> None:
        if term and term.lower() not in seen:
            seen.add(term.lower())
            terms.append(term)

    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = _ARROW.split(line, maxsplit=1)
        if len(parts) == 2 and parts[0].strip() and parts[1].strip():
            wrong, right = parts[0].strip(), parts[1].strip()
            if wrong.lower() != right.lower():
                corrections[wrong.lower()] = right
            add(right)
        else:
            add(line)
    return terms, corrections


def save_user_list(lines: list[str]) -> tuple[int, int]:
    """Speichert die vom Nutzer bearbeitete Liste. Rückgabe: (Begriffe, Korrekturen).

    Verschwindet dabei eine Schreibweise, die nur eine Variante eines verbleibenden
    Begriffs ist (Torben gelöscht, Thorben bleibt), wird daraus eine Korrektur –
    sonst käme die falsche Schreibweise beim nächsten Diktat wieder.
    """
    old_terms = get_learned_terms()
    old_corrections = get_corrections()
    terms, corrections = parse_user_lines(lines)
    kept = {t.lower() for t in terms}
    by_key = {ortho_key(t): t for t in terms if _single_word(t)}
    for old in old_terms:
        if old.lower() in kept or not _single_word(old):
            continue
        right = by_key.get(ortho_key(old))
        if right and old.lower() not in corrections:
            corrections[old.lower()] = right
    # Früher gelernte Korrekturen behalten, solange ihr Ziel noch im Vokabular steht
    # und der Nutzer die falsche Form nicht selbst als Begriff eingetragen hat.
    for wrong, right in old_corrections.items():
        if right.lower() in kept and wrong not in kept and wrong not in corrections:
            corrections[wrong] = right
    corrections = {w: r for w, r in corrections.items() if w not in kept}
    _write(_vocab_path(), terms[-MAX_TERMS:])
    _write(_corrections_path(), corrections)
    return len(terms), len(corrections)


def user_lines() -> list[str]:
    """Die Liste so, wie sie in den Einstellungen steht (Begriffe, dann Korrekturen)."""
    lines = list(get_learned_terms())
    lines += [f"{wrong} -> {right}" for wrong, right in sorted(get_corrections().items())]
    return lines


# ── Hinweis an die Spracherkennung ──────────────────────────────────────────

def prompt_terms(terms: list[str]) -> list[str]:
    """Begriffe, die als Hinweis an Whisper gehen: ohne Doppelte, auf eine Länge
    begrenzt, die Whisper auch wirklich liest (die ersten Begriffe haben Vorrang)."""
    out: list[str] = []
    seen: set[str] = set()
    keys: set[str] = set()
    wrong = get_corrections()
    size = 0
    for term in terms:
        term = (term or "").strip()
        low = term.lower()
        if not term or low in seen or low in wrong:
            continue
        # Zwei Schreibweisen desselben Wortes im Hinweis (Thorben UND Torben) lassen
        # Whisper die falsche wählen – gemessen. Nur die erste geht mit.
        if _single_word(term):
            key = ortho_key(term)
            if key in keys:
                continue
            keys.add(key)
        if len(out) >= PROMPT_MAX_TERMS or size + len(term) + 2 > PROMPT_MAX_CHARS:
            break
        seen.add(low)
        out.append(term)
        size += len(term) + 2
    return out


# ── Korrektur nach der Erkennung ────────────────────────────────────────────

def apply(text: str, extra_terms: list[str] | None = None) -> str:
    """Bringt den Text auf die Schreibweisen des Vokabulars (siehe Modulbeschreibung)."""
    if not text:
        return text
    terms = list(dict.fromkeys([*(extra_terms or []), *get_learned_terms()]))
    corrections = get_corrections()
    if not terms and not corrections:
        return text

    exact = {t.lower() for t in terms}
    by_key: dict[str, str | None] = {}
    for term in terms:
        if not _single_word(term) or not _fuzzy_ok(term):
            continue
        key = ortho_key(term)
        # Zwei Begriffe mit gleichem Schlüssel (Meier und Meyer beide gewollt): nicht raten.
        by_key[key] = term if key not in by_key or (by_key[key] or "").lower() == term.lower() else None

    def fix_word(match: re.Match) -> str:
        word = match.group(0)
        low = word.lower()
        if low in corrections:
            return corrections[low]
        if low.endswith("s") and low[:-1] in corrections:          # "Torbens" → "Thorbens"
            return corrections[low[:-1]] + "s"
        if low in exact or not _fuzzy_ok(word):
            return word
        right = by_key.get(ortho_key(word))
        if right:
            return right
        if low.endswith("s") and low[:-1] not in exact and _fuzzy_ok(word[:-1]):
            right = by_key.get(ortho_key(word[:-1]))
            if right:
                return right + "s"
        return word

    text = _WORD.sub(fix_word, text)

    # Mehrteilige Begriffe und Korrekturen: Leerzeichen/Bindestrich und Groß-/Kleinschreibung angleichen.
    for wrong, right in corrections.items():
        if not _single_word(wrong):
            text = _phrase_pattern(wrong).sub(lambda m, r=right: r, text)
    for term in terms:
        if not _single_word(term):
            text = _phrase_pattern(term).sub(lambda m, r=term: r, text)
    return text


_NEVER = re.compile(r"(?!)")


def _phrase_pattern(phrase: str) -> re.Pattern:
    parts = [re.escape(p) for p in re.split(r"[\s\-]+", phrase.strip()) if p]
    # Ein "Begriff" ohne Buchstaben ("-") ergäbe ein leeres Muster, das überall passt.
    if len(parts) < 2 or not any(_WORD.search(p) for p in parts):
        return _NEVER
    return re.compile(r"(?<!\w)" + r"[\s\-]*".join(parts) + r"(?!\w)", re.IGNORECASE)
