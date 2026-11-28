# Copyright (c) 2026 Thorben Meier. MIT License.
"""Rechnet relative Zeitangaben im Transkript vorab in konkrete Daten um.

Sprachmodelle – vor allem kleine lokale – verrechnen sich bei Angaben wie
"in zwei Wochen, wieder Donnerstag". Deshalb rechnet die App selbst und
schreibt das Ergebnis in Klammern hinter die Angabe:

    "das schicke ich bis nächsten Dienstag (01.12.2026)"

Das Modell muss das Datum dann nur noch abschreiben. Im Zweifel bleibt eine
Angabe unverändert (Vergangenheit, heutiger Wochentag, unvollständiges Datum):
lieber kein Datum als ein falsches.

Erkannt werden deutsche Formulierungen; andere Sprachen bleiben unberührt.
"""

import calendar
import datetime
import re

WEEKDAYS = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
MONTHS = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August",
          "September", "Oktober", "November", "Dezember"]

_WD_RE = "Montag|Dienstag|Mittwoch|Donnerstag|Freitag|Samstag|Sonnabend|Sonntag"
_MON_RE = "|".join(MONTHS)
_COUNT = {"einer": 1, "eine": 1, "1": 1, "zwei": 2, "2": 2, "drei": 3, "3": 3, "vier": 4, "4": 4,
          "fünf": 5, "5": 5, "sechs": 6, "6": 6}
_COUNT_RE = "|".join(_COUNT)

# Hinweise darauf, dass ein Satz von der Vergangenheit spricht ("am Montag war ...").
_PAST = re.compile(
    r"\b(war|waren|hatte|hatten|wurde|wurden|gab|kam|kamen|gestern|letzten|letzte|letzter|"
    r"vergangenen|seit)\b|\b(hat|haben|habe|ist|sind)\b[^.!?]*\b\w*ge\w+(t|en)\b", re.I)

_PATTERN = re.compile(
    # "in zwei Wochen", "in zwei Wochen, wieder Donnerstag"
    rf"(?P<inw>\b(?i:in) (?P<inw_n>{_COUNT_RE}) Wochen?(?:,? (?:wieder |am )?(?P<inw_wd>{_WD_RE}))?)"
    rf"|(?P<ind>\b(?i:in) (?P<ind_n>{_COUNT_RE}|\d+) Tagen)"
    rf"|(?P<endnw>\b(?i:Ende) (?:der )?(?:nächsten|nächster|kommenden|kommender) Woche)"
    rf"|(?P<startnw>\b(?i:Anfang) (?:der )?(?:nächsten|nächster|kommenden|kommender) Woche)"
    rf"|(?P<endtw>\bEnde (?:der|dieser) Woche)"
    # Whisper schreibt "übernächste" gelegentlich getrennt ("über nächste").
    rf"|(?P<w2>\b(?i:über ?nächste[nr]?) Woche(?: (?:am )?(?P<w2_wd>{_WD_RE}))?)"
    rf"|(?P<w1>\b(?i:nächste[nr]?|kommende[nr]?) Woche(?: (?:am )?(?P<w1_wd>{_WD_RE}))?)"
    rf"|(?P<endnm>\bEnde (?:des )?nächsten Monats)"
    rf"|(?P<endtm>\bEnde (?:des|dieses) Monats|\bMonatsende)"
    rf"|(?P<endmon>\bEnde (?P<endmon_m>{_MON_RE}))"
    rf"|(?P<wd>\b(?P<wd_pre>(?i:nächste[nmr]?|kommende[nmr]?|diese[nmr]?|bis|ab|am|zum)) "
    rf"(?P<wd_day>{_WD_RE})\b)"
    rf"|(?P<dayafter>\bübermorgen\b)"
    # nur kleingeschrieben: "Guten Morgen" und "Morgen" am Satzanfang bleiben unberührt
    rf"|(?P<tomorrow>(?<![Gg]uten )\bmorgen\b)"
    rf"|(?P<today>\bheute\b)"
    # "9. Dezember" ohne Jahr
    rf"|(?P<daymon>\b(?P<dm_d>\d{{1,2}})\. (?P<dm_m>{_MON_RE})\b(?! \d{{4}}))"
)


def _wd_index(name: str) -> int:
    return 5 if name == "Sonnabend" else WEEKDAYS.index(name)


def _month_end(year: int, month: int) -> datetime.date:
    return datetime.date(year, month, calendar.monthrange(year, month)[1])


def _resolve_day_month(today: datetime.date, day: int, month: int) -> datetime.date | None:
    """Ergänzt das Jahr: das nächste solche Datum – außer es liegt höchstens 60 Tage zurück."""
    candidates = []
    for year in (today.year - 1, today.year, today.year + 1):
        try:
            candidates.append(datetime.date(year, month, day))
        except ValueError:
            pass
    past = [d for d in candidates if 0 < (today - d).days <= 60]
    future = [d for d in candidates if 0 <= (d - today).days <= 366]
    if future and (not past or (future[0] - today).days <= 180):
        return future[0]
    return past[-1] if past else (future[0] if future else None)


def annotate_dates(text: str, today: datetime.date | None = None) -> str:
    """Schreibt hinter relative Zeitangaben das ausgerechnete Datum in Klammern."""
    if not text:
        return text
    today = today or datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    delta = datetime.timedelta

    def sentence(m: re.Match) -> str:
        start = max(text.rfind(c, 0, m.start()) for c in ".!?") + 1
        ends = [i for i in (text.find(c, m.end()) for c in ".!?") if i != -1]
        return text[start:min(ends) if ends else len(text)]

    def replace(m: re.Match) -> str:
        g = m.groupdict()
        d: datetime.date | None = None
        prefix = ""
        if g["inw"]:
            n = _COUNT[g["inw_n"]]
            d = (monday + delta(weeks=n, days=_wd_index(g["inw_wd"]))) if g["inw_wd"] \
                else today + delta(weeks=n)
        elif g["ind"]:
            d = today + delta(days=_COUNT.get(g["ind_n"]) or int(g["ind_n"]))
        elif g["endnw"]:
            d = monday + delta(days=11)          # Freitag der nächsten Woche
        elif g["startnw"]:
            d = monday + delta(days=7)
        elif g["endtw"]:
            d = monday + delta(days=4)
        elif g["w2"] or g["w1"]:
            n = 2 if g["w2"] else 1
            wd = g["w2_wd"] or g["w1_wd"]
            if wd:
                d = monday + delta(weeks=n, days=_wd_index(wd))
            else:
                d, prefix = monday + delta(weeks=n), "Woche ab "
        elif g["endnm"]:
            d = _month_end(today.year + (today.month == 12), today.month % 12 + 1)
        elif g["endtm"]:
            d = _month_end(today.year, today.month)
        elif g["endmon"]:
            month = MONTHS.index(g["endmon_m"]) + 1
            d = _month_end(today.year + (month < today.month), month)
        elif g["wd"]:
            target = _wd_index(g["wd_day"])
            # "am Montag" kann auch zurückliegen – dann nichts anhängen.
            if g["wd_pre"].lower() == "am" and (
                target == today.weekday() or _PAST.search(sentence(m))
            ):
                return m.group(0)
            d = today + delta(days=(target - today.weekday() - 1) % 7 + 1)
        elif g["dayafter"]:
            d = today + delta(days=2)
        elif g["tomorrow"]:
            d = today + delta(days=1)
        elif g["today"]:
            d = today
        elif g["daymon"]:
            d = _resolve_day_month(today, int(g["dm_d"]), MONTHS.index(g["dm_m"]) + 1)
        if d is None:
            return m.group(0)
        return f"{m.group(0)} ({prefix}{d:%d.%m.%Y})"

    return _PATTERN.sub(replace, text)
