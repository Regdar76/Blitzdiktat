"""
Speichert transkribierte Texte lokal als .txt-Dateien und bereinigt alte Einträge.
Spiegelt die Logik von audio_recorder.py für Audiodateien.
"""

import os
import time
import datetime

MAX_AGE_DAYS = 14


def transcripts_dir() -> str:
    """Permanenter Ordner für alle Transkriptionen: %LOCALAPPDATA%\\Blitzdiktat\\Transkriptionen"""
    base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    path = os.path.join(base, "Blitzdiktat", "Transkriptionen")
    os.makedirs(path, exist_ok=True)
    return path


def save_transcript(text: str, workflow_name: str = "") -> str:
    """
    Speichert *text* als .txt-Datei im Transkriptionsordner.
    Gibt den Dateipfad zurück.
    """
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"blitztext_{ts}.txt"
    path = os.path.join(transcripts_dir(), filename)

    header_lines = [f"Datum: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"]
    if workflow_name:
        header_lines.append(f"Workflow: {workflow_name}")
    header_lines.append("-" * 40)
    header = "\n".join(header_lines) + "\n\n"

    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(header + text)
    except Exception:
        pass
    return path


def cleanup_old_transcripts() -> None:
    """Löscht .txt- und .pdf-Dateien im Transkriptionsordner, die älter als MAX_AGE_DAYS Tage sind."""
    folder = transcripts_dir()
    cutoff = time.time() - MAX_AGE_DAYS * 86400
    try:
        for name in os.listdir(folder):
            if not (name.lower().endswith(".txt") or name.lower().endswith(".pdf")):
                continue
            path = os.path.join(folder, name)
            try:
                if os.path.getmtime(path) < cutoff:
                    os.remove(path)
            except Exception:
                pass
    except Exception:
        pass


# ---------------------------------------------------------------------------
# PDF-Erzeugung für Blitzdiktat Protokoll
# ---------------------------------------------------------------------------

def _xml_escape(text: str) -> str:
    """Escapet Sonderzeichen für ReportLab-Paragraphen."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _md_inline(text: str) -> str:
    """Wandelt **bold** in ReportLab-XML um (nach XML-Escaping)."""
    import re
    escaped = _xml_escape(text)
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)


def save_protocol_as_pdf(text: str) -> str:
    """
    Rendert den Protokoll-Markdown-Text als PDF und speichert ihn im
    Transkriptionsordner. Gibt den Dateipfad zurueck.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_LEFT
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer,
            HRFlowable, Table, TableStyle,
        )
    except ImportError:
        return ""

    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = os.path.join(transcripts_dir(), f"protokoll_{ts}.pdf")

    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
        title="Blitzdiktat Protokoll",
    )

    base = getSampleStyleSheet()

    st_h1 = ParagraphStyle(
        "BT_H1", parent=base["Heading1"],
        fontSize=15, leading=20, spaceAfter=6, textColor=colors.HexColor("#111827"),
    )
    st_h2 = ParagraphStyle(
        "BT_H2", parent=base["Heading2"],
        fontSize=12, leading=16, spaceBefore=10, spaceAfter=4,
        textColor=colors.HexColor("#1F2937"),
    )
    st_normal = ParagraphStyle(
        "BT_Normal", parent=base["Normal"],
        fontSize=10, leading=14, spaceAfter=3,
    )
    st_bullet = ParagraphStyle(
        "BT_Bullet", parent=base["Normal"],
        fontSize=10, leading=14, spaceAfter=2,
        leftIndent=14,
    )

    story = []
    lines = text.split("\n")
    table_rows: list[list[str]] = []

    def _flush_table() -> None:
        if not table_rows:
            return
        col_count = max(len(r) for r in table_rows)
        col_w = (doc.width) / col_count
        col_widths = [col_w] * col_count

        tbl = Table(table_rows, colWidths=col_widths, hAlign="LEFT")
        tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor("#E5E7EB")),
            ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE",      (0, 0), (-1, -1), 9),
            ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING",   (0, 0), (-1, -1), 6),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 8))
        table_rows.clear()

    import re

    for raw_line in lines:
        line = raw_line.rstrip()

        # Tabellenzeile
        if line.strip().startswith("|") and line.strip().endswith("|"):
            # Separator-Zeile |---|---| überspringen
            if re.match(r"^\s*\|[-| :]+\|\s*$", line):
                continue
            cells = [c.strip() for c in line.strip()[1:-1].split("|")]
            table_rows.append(cells)
            continue

        # Vor jedem Nicht-Tabellen-Element ggf. Tabelle ausgeben
        _flush_table()

        stripped = line.strip()

        if not stripped:
            story.append(Spacer(1, 4))

        elif stripped.startswith("## "):
            story.append(Paragraph(_xml_escape(stripped[3:]), st_h1))

        elif stripped.startswith("### "):
            story.append(Paragraph(_xml_escape(stripped[4:]), st_h2))

        elif stripped == "---":
            story.append(HRFlowable(
                width="100%", thickness=0.5,
                color=colors.HexColor("#D1D5DB"),
                spaceBefore=4, spaceAfter=4,
            ))

        elif stripped.startswith("- "):
            story.append(Paragraph(
                "• " + _md_inline(stripped[2:]),
                st_bullet,
            ))

        else:
            story.append(Paragraph(_md_inline(stripped), st_normal))

    _flush_table()  # letzte Tabelle, falls am Ende

    try:
        doc.build(story)
    except Exception:
        return ""
    return path
