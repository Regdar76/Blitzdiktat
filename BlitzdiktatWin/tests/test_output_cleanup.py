# Copyright (c) 2026 Thorben Meier. MIT License.
"""Tests für die Nachbearbeitung von Modellausgaben (services/output_cleanup)."""

from services.output_cleanup import clean_protocol, strip_reasoning, strip_wrapping


def test_sternchen_listen_werden_zu_strichen():
    out = clean_protocol("### Besprochene Punkte\n* Punkt eins\n*   Punkt zwei\n• Punkt drei")
    assert out.splitlines()[1:] == ["- Punkt eins", "- Punkt zwei", "- Punkt drei"]


def test_fettschrift_bleibt_erhalten():
    assert clean_protocol("**Datum:** 26.11.2026") == "**Datum:** 26.11.2026"


def test_vierte_ueberschriftenebene_wird_fette_zeile():
    assert clean_protocol("#### Estrich Halle 2\n- Punkt") == "**Estrich Halle 2**\n- Punkt"


def test_codeblock_zaeune_werden_entfernt():
    assert clean_protocol("```markdown\n## Protokoll\n```") == "## Protokoll"


def test_leere_abschnitte_und_teilnehmerzeile_entfallen():
    text = (
        "## Protokoll\n\n**Datum:** 18.12.2026\n**Teilnehmer:** –\n\n"
        "### Zusammenfassung\nKurze Abstimmung.\n\n"
        "### Entscheidungen\n- –\n\n"
        "### Offene Aufgaben\n- Paletten umlagern — Verantwortlich: –, Deadline: 18.12.2026\n\n"
        "### Nächster Termin\n–"
    )
    out = clean_protocol(text)
    assert "Teilnehmer" not in out
    assert "### Entscheidungen" not in out
    assert "### Nächster Termin" not in out
    assert "### Offene Aufgaben" in out and "Paletten umlagern" in out
    assert "### Zusammenfassung\nKurze Abstimmung." in out


def test_gefuellte_abschnitte_bleiben():
    text = "### Entscheidungen\n- Geräte werden bestellt\n\n### Nächster Termin\nDienstag, 23.02.2027, 14 Uhr"
    assert clean_protocol(text) == text


def test_anfuehrungszeichen_um_die_ganze_antwort_entfallen():
    assert strip_wrapping('"Guten Tag,\n\nbitte liefern Sie bis Mittwoch."') == \
        "Guten Tag,\n\nbitte liefern Sie bis Mittwoch."
    assert strip_wrapping("„Guten Tag, bitte liefern Sie.“") == "Guten Tag, bitte liefern Sie."


def test_zitate_im_text_bleiben():
    text = '"Dringend" stand im Ticket, mehr nicht. Das Formular heißt "Störung".'
    assert strip_wrapping(text) == text


def test_denkblock_wird_entfernt():
    assert strip_reasoning("<think>\nErst überlegen …\n</think>\n\nGuten Tag,") == "Guten Tag,"
    assert strip_reasoning("Guten Tag,") == "Guten Tag,"
    assert strip_reasoning(None) == ""
