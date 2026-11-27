# Copyright (c) 2026 Thorben Meier. MIT License.
"""Tests für die Vorab-Berechnung relativer Zeitangaben (services/date_annotator)."""

import datetime as dt

import pytest

from services.date_annotator import annotate_dates

DO = dt.date(2026, 11, 26)   # Donnerstag
DI = dt.date(2027, 2, 2)     # Dienstag
FR = dt.date(2026, 12, 18)   # Freitag


@pytest.mark.parametrize("today, text, expected", [
    (DO, "Das schicke ich bis nächsten Dienstag.", "bis nächsten Dienstag (01.12.2026)"),
    (DO, "Das schicke ich bis Freitag.", "bis Freitag (27.11.2026)"),
    (DO, "Dann beauftrage ich das heute noch.", "heute (26.11.2026) noch"),
    (DO, "Sollte bis Ende nächster Woche erledigt sein.", "Ende nächster Woche (04.12.2026)"),
    (DO, "Nächste Besprechung in zwei Wochen, wieder Donnerstag, 9 Uhr.",
     "in zwei Wochen, wieder Donnerstag (10.12.2026)"),
    (DO, "Anfang nächster Woche kommt der Estrich.", "Anfang nächster Woche (30.11.2026)"),
    (DO, "Ende der Woche kommt der Maler.", "Ende der Woche (27.11.2026)"),
    (DO, "Das ist der 9. Dezember vormittags.", "9. Dezember (09.12.2026)"),
    (DO, "Abgabe bis zum 8. Januar.", "8. Januar (08.01.2027)"),
    (DO, "Die Begehung am 3. November lief gut.", "3. November (03.11.2026)"),
    (DI, "Den Test mache ich übermorgen.", "übermorgen (04.02.2027)"),
    (DI, "Ich informiere morgen die Abteilungsleiter.", "morgen (03.02.2027)"),
    (DI, "Die restlichen stellen wir bis Ende Februar um.", "Ende Februar (28.02.2027)"),
    (DI, "Verschoben von nächstem Montag auf später.", "nächstem Montag (08.02.2027)"),
    (DI, "Wir sehen uns in drei Wochen wieder, gleicher Tag.", "in drei Wochen (23.02.2027)"),
    (FR, "Die Scanner kommen nächste Woche Mittwoch zurück.", "nächste Woche Mittwoch (23.12.2026)"),
    (FR, "Das Hochregal wird am Montag gesperrt.", "am Montag (21.12.2026)"),
    (FR, "Die Geräte kommen nächste Woche.", "nächste Woche (Woche ab 21.12.2026)"),
    (dt.date(2026, 12, 30), "Abgabe Ende des Monats.", "Ende des Monats (31.12.2026)"),
    (dt.date(2026, 12, 30), "Abgabe Ende nächsten Monats.", "Ende nächsten Monats (31.01.2027)"),
    (dt.date(2026, 12, 30), "Abgabe in 10 Tagen.", "in 10 Tagen (09.01.2027)"),
    (dt.date(2026, 12, 28), "Kommenden Sonnabend ist frei.", "Kommenden Sonnabend (02.01.2027)"),
    (dt.date(2027, 4, 14), "Daten bis übernächste Woche Freitag.",
     "übernächste Woche Freitag (30.04.2027)"),
    # Whisper schreibt "übernächste" gelegentlich getrennt
    (dt.date(2027, 4, 14), "Daten bis über nächste Woche Freitag.",
     "über nächste Woche Freitag (30.04.2027)"),
])
def test_angabe_bekommt_datum(today, text, expected):
    assert expected in annotate_dates(text, today)


@pytest.mark.parametrize("today, text", [
    (DO, "Guten Morgen zusammen, morgens ist es kalt."),
    (DO, "Morgen ist auch noch ein Tag."),                 # Satzanfang: mehrdeutig
    (DO, "Die Begehung war am Dienstag."),                 # Vergangenheit
    (DO, "Er hat am Dienstag angerufen."),                 # Perfekt
    (DO, "Die Heizung ist seit Montag kalt."),             # kein Termin
    (DO, "Die haben uns für Montag die Server zugesagt."),
    (DO, "Und heute, am Donnerstag, kam die Absage."),     # heutiger Wochentag
    (DO, "Das war am 3. November 2026 so."),               # Jahr steht schon da
    (DI, "Termin am 29. Februar."),                        # gibt es 2027 nicht
    (DO, "Der Umzug bleibt bei Mitte Dezember."),
    (DO, ""),
])
def test_bleibt_unveraendert(today, text):
    out = annotate_dates(text, today)
    # "heute" darf ein Datum bekommen, alles andere bleibt wie es ist
    assert out.replace(" (26.11.2026)", "") == text


def test_mehrere_angaben_in_einem_text():
    text = ("Herr Aydin, bitte bestellen Sie die Geräte bis Freitag. "
            "Den Test mache ich übermorgen. Wir sehen uns in drei Wochen wieder.")
    out = annotate_dates(text, DI)
    assert "(05.02.2027)" in out and "(04.02.2027)" in out and "(23.02.2027)" in out


def test_ohne_datum_gilt_heute():
    assert f"({dt.date.today():%d.%m.%Y})" in annotate_dates("Das mache ich heute noch.")
