# Copyright (c) 2026 Thorben Meier. MIT License.
"""Prompt-Fassungen für kleine lokale Modelle (Versuch, noch nicht in der App).

Unterschiede zu den App-Prompts (die auf gpt-4o zugeschnitten sind):
- kurze, nummerierte Regeln statt Fließtext
- das Transkript steht in Anführungszeichen-Blöcken, damit das Modell es nicht
  als an sich gerichtete Nachricht versteht
- keine Platzhalter in eckigen Klammern in der Vorlage (kleine Modelle
  schreiben sie ab)
- Datumsangaben rechnet nicht das Modell, sondern kalender(): das Modell liest
  nur noch ab
- saeubern() bringt die Ausgabe in die Form, die der PDF-Export versteht
"""

import calendar
import datetime
import re

WOCHENTAGE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August",
          "September", "Oktober", "November", "Dezember"]
_WOCHE = {0: "diese Woche", 1: "nächste Woche", 2: "in zwei Wochen",
          3: "in drei Wochen", 4: "in vier Wochen"}
_ZAHL = {1: "einer Woche", 2: "zwei Wochen", 3: "drei Wochen", 4: "vier Wochen"}


def _fmt(d: datetime.date) -> str:
    return f"{WOCHENTAGE[d.weekday()]}, {d:%d.%m.%Y}"


def _monatsende(jahr: int, monat: int) -> datetime.date:
    return datetime.date(jahr, monat, calendar.monthrange(jahr, monat)[1])


def kalender(heute: datetime.date, tage: int = 29) -> str:
    """Nachschlagetabelle: relative Zeitangabe → Datum, vom Aufnahmedatum aus."""
    montag = heute - datetime.timedelta(days=heute.weekday())
    z = ["Kalender zum Ablesen (links das Datum, rechts wie es im Gespräch heißt):"]
    gesehen: set[int] = set()
    for k in range(tage):
        d = heute + datetime.timedelta(days=k)
        name = WOCHENTAGE[d.weekday()]
        woche = (d - montag).days // 7
        marken = []
        if k == 0:
            marken.append("heute")
        elif k == 1:
            marken.append("morgen")
        elif k == 2:
            marken.append("übermorgen")
        if k >= 1 and d.weekday() not in gesehen:
            gesehen.add(d.weekday())
            marken.append(f"am {name}, bis {name}, nächsten {name}")
        if k >= 1 and woche in _WOCHE:
            marken.append(f"{_WOCHE[woche]} {name}")
        if k and k % 7 == 0:
            marken.append(f"heute in {_ZAHL[k // 7]}")
        z.append(f"{_fmt(d)} = " + "; ".join(marken))

    freitag = montag + datetime.timedelta(days=4)
    z.append("")
    if heute <= freitag:
        z.append(f"Ende dieser Woche = {_fmt(freitag)}")
    z.append(f"Ende nächster Woche = {_fmt(freitag + datetime.timedelta(days=7))}")
    j, m = heute.year, heute.month
    for i in range(3):
        mm = (m - 1 + i) % 12 + 1
        jj = j + (m - 1 + i) // 12
        ende = _monatsende(jj, mm)
        zusatz = " (Ende des Monats)" if i == 0 else " (Ende nächsten Monats)" if i == 1 else ""
        z.append(f"Ende {MONATE[mm - 1]}{zusatz} = {_fmt(ende)}")

    # Jahr für Angaben wie "9. Dezember": das nächste solche Datum ab heute.
    dieses = ", ".join(MONATE[m - 1:])
    z.append("")
    if m == 1:
        z.append(f"Ein Datum ohne Jahr bekommt das Jahr {j}.")
    else:
        davor = ", ".join(MONATE[:m - 1])
        z.append(f"Ein Datum ohne Jahr: {dieses} → Jahr {j}; {davor} → Jahr {j + 1}.")
    return "\n".join(z)


_WT_RE = "Montag|Dienstag|Mittwoch|Donnerstag|Freitag|Samstag|Sonnabend|Sonntag"
_MON_RE = "|".join(MONATE)
_N = {"einer": 1, "eine": 1, "1": 1, "zwei": 2, "2": 2, "drei": 3, "3": 3, "vier": 4, "4": 4,
      "fünf": 5, "5": 5, "sechs": 6, "6": 6}
_N_RE = "|".join(_N)
_VERGANGEN = re.compile(
    r"\b(war|waren|hatte|hatten|wurde|wurden|gab|kam|kamen|gestern|letzten|letzte|letzter|"
    r"vergangenen|seit)\b|\b(hat|haben|habe|ist|sind)\b[^.!?]*\b\w*ge\w+(t|en)\b", re.I)

_DATUM_RE = re.compile(
    rf"(?P<inw>\b(?i:in) (?P<inw_n>{_N_RE}) Wochen?(?:,? (?:wieder |am )?(?P<inw_wt>{_WT_RE}))?)"
    rf"|(?P<int>\b(?i:in) (?P<int_n>{_N_RE}|\d+) Tagen)"
    rf"|(?P<endnw>\b(?i:Ende) (?:der )?(?:nächsten|nächster|kommenden|kommender) Woche)"
    rf"|(?P<anfnw>\b(?i:Anfang) (?:der )?(?:nächsten|nächster|kommenden|kommender) Woche)"
    rf"|(?P<enddw>\bEnde (?:der|dieser) Woche)"
    rf"|(?P<uenw>\b(?i:über ?nächste[nr]?) Woche(?: (?:am )?(?P<uenw_wt>{_WT_RE}))?)"
    rf"|(?P<nw>\b(?i:nächste[nr]?|kommende[nr]?) Woche(?: (?:am )?(?P<nw_wt>{_WT_RE}))?)"
    rf"|(?P<endnm>\bEnde (?:des )?nächsten Monats)"
    rf"|(?P<enddm>\bEnde (?:des|dieses) Monats|\bMonatsende)"
    rf"|(?P<endmon>\bEnde (?P<endmon_m>{_MON_RE}))"
    rf"|(?P<wt>\b(?P<wt_vor>(?i:nächste[nmr]?|kommende[nmr]?|diese[nmr]?|bis|ab|am|zum)) "
    rf"(?P<wt_tag>{_WT_RE})\b)"
    rf"|(?P<ueberm>\bübermorgen\b)"
    rf"|(?P<morgen>(?<![Gg]uten )\bmorgen\b)"
    rf"|(?P<heute>\bheute\b)"
    rf"|(?P<tagmon>\b(?P<tm_t>\d{{1,2}})\. (?P<tm_m>{_MON_RE})\b(?! \d{{4}}))"
)


def _wt_index(name: str) -> int:
    return 5 if name == "Sonnabend" else WOCHENTAGE.index(name)


def _naechstes_datum(heute: datetime.date, tag: int, monat: int) -> datetime.date | None:
    """Jahr ergänzen: das nächste solche Datum – außer es liegt höchstens 60 Tage zurück."""
    kandidaten = []
    for jahr in (heute.year - 1, heute.year, heute.year + 1):
        try:
            kandidaten.append(datetime.date(jahr, monat, tag))
        except ValueError:
            pass
    zurueck = [d for d in kandidaten if 0 < (heute - d).days <= 60]
    voraus = [d for d in kandidaten if 0 <= (d - heute).days <= 366]
    if voraus and (not zurueck or (voraus[0] - heute).days <= 180):
        return voraus[0]
    return zurueck[-1] if zurueck else (voraus[0] if voraus else None)


def datum_annotieren(text: str, heute: datetime.date) -> str:
    """Schreibt hinter relative Zeitangaben das ausgerechnete Datum in Klammern.

    Das Rechnen übernimmt damit die App; das Modell muss das Datum nur noch
    abschreiben. Im Zweifel (Vergangenheit, heutiger Wochentag) bleibt die
    Angabe unverändert.
    """
    montag = heute - datetime.timedelta(days=heute.weekday())
    tage = datetime.timedelta

    def satz(m: re.Match) -> str:
        a = max(text.rfind(c, 0, m.start()) for c in ".!?") + 1
        enden = [i for i in (text.find(c, m.end()) for c in ".!?") if i != -1]
        return text[a:min(enden) if enden else len(text)]

    def ersetze(m: re.Match) -> str:
        g = m.lastgroup and m.groupdict()
        d = None
        zusatz = ""
        if g["inw"]:
            n = _N[g["inw_n"]]
            d = (montag + tage(weeks=n, days=_wt_index(g["inw_wt"]))) if g["inw_wt"] \
                else heute + tage(weeks=n)
        elif g["int"]:
            d = heute + tage(days=_N.get(g["int_n"]) or int(g["int_n"]))
        elif g["endnw"]:
            d = montag + tage(days=11)
        elif g["anfnw"]:
            d = montag + tage(days=7)
        elif g["enddw"]:
            d = montag + tage(days=4)
        elif g["uenw"] or g["nw"]:
            n = 2 if g["uenw"] else 1
            wt = g["uenw_wt"] or g["nw_wt"]
            if wt:
                d = montag + tage(weeks=n, days=_wt_index(wt))
            else:
                d, zusatz = montag + tage(weeks=n), "Woche ab "
        elif g["endnm"]:
            m2 = heute.month % 12 + 1
            d = _monatsende(heute.year + (heute.month == 12), m2)
        elif g["enddm"]:
            d = _monatsende(heute.year, heute.month)
        elif g["endmon"]:
            mon = MONATE.index(g["endmon_m"]) + 1
            d = _monatsende(heute.year + (mon < heute.month), mon)
        elif g["wt"]:
            ziel = _wt_index(g["wt_tag"])
            vor = g["wt_vor"].lower()
            if vor == "am" and (ziel == heute.weekday() or _VERGANGEN.search(satz(m))):
                return m.group(0)
            d = heute + tage(days=(ziel - heute.weekday() - 1) % 7 + 1)
        elif g["ueberm"]:
            d = heute + tage(days=2)
        elif g["morgen"]:
            d = heute + tage(days=1)
        elif g["heute"]:
            d = heute
        elif g["tagmon"]:
            d = _naechstes_datum(heute, int(g["tm_t"]), MONATE.index(g["tm_m"]) + 1)
        if d is None:
            return m.group(0)
        return f"{m.group(0)} ({zusatz}{d:%d.%m.%Y})"

    return _DATUM_RE.sub(ersetze, text)


DAMPF_SYSTEM = (
    "Du machst aus einem verärgert gesprochenen Diktat eine sachliche Nachricht, die die "
    "sprechende Person selbst abschicken kann. Empfänger ist die Person oder Firma, über die "
    "sie sich ärgert.\n\n"
    "Regeln:\n"
    "1. Schreibe aus Sicht der sprechenden Person (ich/wir) an den Empfänger (Sie). Du sprichst "
    "nicht mit der sprechenden Person, du tröstest nicht und kommentierst nichts.\n"
    "2. Formuliere alles neu in höflicher Geschäftssprache. Übernimm keinen Satz wörtlich. "
    "Schimpfen, Ausrufe, Beleidigungen, Spott und Unterstellungen entfallen ganz.\n"
    "3. Alle Fakten bleiben unverändert erhalten: was passiert ist, wie oft, Zahlen, "
    "Wochentage, Fristen, Namen.\n"
    "4. Jede Forderung und jede Frist bleibt erhalten. Angekündigte Folgen werden zu einem "
    "ruhigen Hinweis (\"behalte ich mir vor, …\").\n"
    "5. Erfinde nichts dazu: keine neuen Fakten, Forderungen, Beträge, Angebote oder Namen.\n"
    "6. Offensichtliche Hörfehler im Transkript schreibst du richtig.\n"
    "7. Aufbau: Anrede – was passiert ist – was das für uns bedeutet – was wir erwarten und bis "
    "wann – was sonst geschieht – \"Mit freundlichen Grüßen\". Kennst du den Namen des "
    "Empfängers nicht, lautet die Anrede \"Guten Tag,\".\n"
    "8. Keine eckigen Klammern, keine Platzhalter, keine Betreffzeile. Gib nur die Nachricht "
    "aus – ohne Einleitung, ohne Anführungszeichen, ohne Erklärung danach.\n\n"
    "Beispiel\n"
    "Transkript: Das gibt's doch nicht, der Paketdienst hat schon wieder die Lieferung beim "
    "Nachbarn abgegeben, obwohl ich extra geschrieben habe nur persönlich. Das ist das zweite "
    "Mal diese Woche, sind die zu blöd zum Lesen? Wenn das noch einmal passiert, kündige ich "
    "den Vertrag, und die 30 Euro Expresszuschlag will ich zurück.\n"
    "Nachricht:\n"
    "Guten Tag,\n\n"
    "meine Sendung wurde erneut bei einem Nachbarn abgegeben, obwohl ich ausdrücklich die "
    "persönliche Zustellung vereinbart hatte. Das ist bereits das zweite Mal in dieser Woche.\n\n"
    "Ich bitte Sie, die persönliche Zustellung künftig sicherzustellen und mir den "
    "Expresszuschlag von 30 Euro zu erstatten. Sollte sich der Vorfall wiederholen, behalte "
    "ich mir vor, den Vertrag zu kündigen.\n\n"
    "Mit freundlichen Grüßen"
)


def dampf_user(transkript: str) -> str:
    return (
        f'Transkript des Diktats:\n"""\n{transkript}\n"""\n\n'
        "Schreibe jetzt nur die fertige Nachricht."
    )


PROTOKOLL_SYSTEM = (
    "Du schreibst aus dem Transkript einer Besprechung ein Protokoll auf Deutsch.\n\n"
    "Regeln:\n"
    "1. Nimm nur auf, was gesagt wurde. Erfinde nichts und lass nichts Wichtiges weg.\n"
    "2. Zahlen, Beträge, Maße, Raumnummern und Namen übernimmst du Zeichen für Zeichen aus dem "
    "Transkript. Namen schreibst du genau so wie dort.\n"
    "3. Datumsangaben: Im Transkript steht hinter Zeitangaben das ausgerechnete Datum in "
    "Klammern, zum Beispiel \"bis Freitag (05.02.2027)\". Schreibe im Protokoll immer dieses "
    "Datum und rechne nie selbst. Angaben ohne Klammer wie \"Mitte Dezember\" übernimmst du "
    "wörtlich.\n"
    "4. Offene Aufgaben: Jede Zusage (\"das mache ich\", \"das schicke ich\", \"bitte "
    "bestellen Sie\") ist eine Aufgabe. Verantwortliche sind nur Namen oder Rollen aus dem "
    "Transkript. Ist nicht eindeutig, wer etwas übernimmt, schreibe \"–\". Gibt es keine "
    "Frist, schreibe \"–\". Wer abgesagt hat, ist kein Teilnehmer.\n"
    "5. Form: Überschriften nur mit \"##\" und \"###\". Aufzählungen beginnen mit \"- \". Keine "
    "Sternchen-Listen, keine Tabellen, keine Codeblöcke, keine eckigen Klammern.\n"
    "6. Lass weg, was nicht vorkommt: keine Namen genannt → keine Zeile \"Teilnehmer\". Kein "
    "Folgetermin genannt → kein Abschnitt \"Nächster Termin\". Keine Entscheidungen → kein "
    "Abschnitt \"Entscheidungen\".\n"
    "7. Gib nur das Protokoll aus, ohne Einleitung und ohne Nachwort.\n\n"
    "Aufbau – genau diese Überschriften in dieser Reihenfolge:\n\n"
    "## Protokoll\n\n"
    "**Datum:** das Aufnahmedatum\n"
    "**Thema:** das Thema in wenigen Worten\n"
    "**Teilnehmer:** die genannten Namen mit Rolle, durch Komma getrennt\n\n"
    "---\n\n"
    "### Zusammenfassung\n"
    "4 bis 6 Sätze für jemanden, der nicht dabei war: Anlass, wichtigste Inhalte, Ergebnis, "
    "nächste Schritte.\n\n"
    "### Besprochene Punkte\n"
    "- ein Punkt je Zeile, mit den genannten Zahlen\n\n"
    "### Entscheidungen\n"
    "- eine Entscheidung je Zeile\n\n"
    "### Offene Aufgaben\n"
    "- Aufgabe — Verantwortlich: Name, Deadline: TT.MM.JJJJ\n\n"
    "### Nächster Termin\n"
    "Wochentag, TT.MM.JJJJ, Uhrzeit, Ort"
)


def protokoll_user(transkript: str, heute: datetime.date) -> str:
    return (
        f"Aufnahmedatum: {_fmt(heute)}\n\n"
        f'Transkript der Besprechung:\n"""\n{datum_annotieren(transkript, heute)}\n"""\n\n'
        "Schreibe jetzt nur das Protokoll."
    )


_LEER = re.compile(r"^[\s\-–—*•.]*(keine[rs]?|nicht genannt|entfällt|n/a)?[\s\-–—.]*$", re.I)


def _leeres_entfernen(zeilen: list[str]) -> list[str]:
    """Streicht 'Teilnehmer: –' und Abschnitte, in denen nur ein Strich steht."""
    out: list[str] = []
    i = 0
    while i < len(zeilen):
        z = zeilen[i]
        m = re.match(r"^\*\*(Teilnehmer|Thema):\*\*(.*)$", z.strip())
        if m and _LEER.match(m.group(2)):
            i += 1
            continue
        if z.startswith("### "):
            j = i + 1
            while j < len(zeilen) and not zeilen[j].startswith("#"):
                j += 1
            if all(_LEER.match(x) for x in zeilen[i + 1:j]):
                i = j
                continue
        out.append(z)
        i += 1
    return out


def saeubern(text: str) -> str:
    """Bringt die Modellausgabe in die Form, die der PDF-Export versteht."""
    zeilen = []
    for zeile in text.strip().splitlines():
        if zeile.strip().startswith("```"):
            continue
        zeile = re.sub(r"^(\s*)[*•]\s+", r"\1- ", zeile)
        m = re.match(r"^\s*#{4,}\s+(.*)$", zeile)
        if m:
            zeile = f"**{m.group(1).strip()}**"
        zeilen.append(zeile)
    zeilen = _leeres_entfernen(zeilen)
    out = "\n".join(zeilen).strip()
    for auf, zu in (('"', '"'), ("„", "“"), ("»", "«")):
        if out.startswith(auf) and out.endswith(zu) and out.count(auf) == 1:
            out = out[1:-1].strip()
    return out


if __name__ == "__main__":
    print(kalender(datetime.date(2026, 11, 26)))
