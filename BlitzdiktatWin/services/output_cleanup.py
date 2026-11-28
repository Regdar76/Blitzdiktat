# Copyright (c) 2026 Thorben Meier. MIT License.
"""Bringt Modellausgaben in die Form, die Blitzdiktat weiterverarbeitet.

Der PDF-Export (transcript_store) kennt nur "## ", "### ", "- " und "---".
Vor allem kleine lokale Modelle halten sich nicht immer daran: Sternchen-Listen,
"####"-Überschriften, Codeblöcke, leere Abschnitte mit einem Strich oder die
ganze Antwort in Anführungszeichen. Diese Funktionen räumen das auf, ohne
Inhalt zu verändern.
"""

import re

_THINK = re.compile(r"^\s*<think>.*?</think>\s*", re.S | re.I)
_EMPTY = re.compile(r"^[\s\-–—*•.]*(keine[rs]?|nicht genannt|entfällt|n/a)?[\s\-–—.]*$", re.I)
_QUOTES = (('"', '"'), ("„", "“"), ("“", "”"), ("»", "«"), ("«", "»"))


def strip_reasoning(text: str) -> str:
    """Entfernt einen vorangestellten <think>…</think>-Block (manche lokale Server)."""
    return _THINK.sub("", text or "", count=1).strip()


def strip_wrapping(text: str) -> str:
    """Entfernt Codeblock-Zäune und Anführungszeichen um die gesamte Antwort."""
    lines = [ln for ln in (text or "").strip().splitlines() if not ln.strip().startswith("```")]
    out = "\n".join(lines).strip()
    for opening, closing in _QUOTES:
        if len(out) > 1 and out.startswith(opening) and out.endswith(closing):
            inner = out[1:-1]
            # nur wenn die Zeichen wirklich die ganze Antwort einrahmen
            if opening not in inner and closing not in inner:
                out = inner.strip()
            break
    return out


def _drop_empty_parts(lines: list[str]) -> list[str]:
    """Streicht 'Teilnehmer: –' und Abschnitte, in denen nur ein Strich steht."""
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^\*\*(Teilnehmer|Thema):\*\*(.*)$", line.strip())
        if m and _EMPTY.match(m.group(2)):
            i += 1
            continue
        if line.startswith("### "):
            j = i + 1
            while j < len(lines) and not lines[j].startswith("#"):
                j += 1
            if all(_EMPTY.match(x) for x in lines[i + 1:j]):
                i = j
                continue
        out.append(line)
        i += 1
    return out


def clean_protocol(text: str) -> str:
    """Normalisiert ein Protokoll für Anzeige und PDF-Export."""
    lines: list[str] = []
    for line in strip_wrapping(text).splitlines():
        # "* Punkt" / "• Punkt" → "- Punkt"
        line = re.sub(r"^(\s*)[*•]\s+", r"\1- ", line)
        # "#### Unterpunkt" kennt der PDF-Export nicht → fette Zeile
        m = re.match(r"^\s*#{4,}\s+(.*)$", line)
        if m:
            line = f"**{m.group(1).strip()}**"
        lines.append(line)
    return "\n".join(_drop_empty_parts(lines)).strip()
