# Copyright (c) 2026 Thorben Meier. MIT License.
r"""
Notiz-Fenster: Entwurf sichern und Text exportieren.

* Der Entwurf liegt unter %LOCALAPPDATA%\Blitzdiktat\notiz_entwurf.txt und
  wird beim nächsten Öffnen wiederhergestellt.
* Export als Textdatei (UTF-8 mit Kennung, damit Word und Editor Umlaute
  richtig lesen) oder als PDF (reportlab, wie das Protokoll).
"""

import datetime
import os
from xml.sax.saxutils import escape

DRAFT_NAME = "notiz_entwurf.txt"


def _base_dir() -> str:
    base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    path = os.path.join(base, "Blitzdiktat")
    os.makedirs(path, exist_ok=True)
    return path


def draft_path() -> str:
    return os.path.join(_base_dir(), DRAFT_NAME)


def load_draft() -> str:
    try:
        with open(draft_path(), "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def save_draft(text: str) -> None:
    """Sichert den Entwurf; ein leerer Text löscht ihn."""
    path = draft_path()
    try:
        if text.strip():
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
        elif os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


def suggested_filename(extension: str) -> str:
    stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    return f"Notiz_{stamp}.{extension.lstrip('.')}"


def export_text(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8-sig", newline="\r\n") as f:
        f.write(text)


def export_pdf(path: str, text: str) -> bool:
    """Schreibt den Text als PDF (A4). False, wenn reportlab fehlt."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    except ImportError:
        return False

    doc = SimpleDocTemplate(
        path, pagesize=A4, leftMargin=2.5 * cm, rightMargin=2.5 * cm,
        topMargin=2.5 * cm, bottomMargin=2.5 * cm, title="Blitzdiktat Notiz",
    )
    style = ParagraphStyle("BD_Note", parent=getSampleStyleSheet()["Normal"], fontSize=11, leading=16, spaceAfter=6)
    story = []
    for block in text.replace("\r\n", "\n").split("\n"):
        if block.strip():
            story.append(Paragraph(escape(block).replace("  ", "&nbsp;&nbsp;"), style))
        else:
            story.append(Spacer(1, 8))
    doc.build(story or [Spacer(1, 1)])
    return True


def join_dictation(existing: str, new: str) -> str:
    """Hängt diktierten Text an: mit Leerzeichen, nach einem Zeilenumbruch ohne."""
    new = new.strip()
    if not new:
        return existing
    if not existing or existing.endswith(("\n", " ")):
        return existing + new
    return existing + " " + new
