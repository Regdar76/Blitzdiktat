# Copyright (c) 2026 Thorben Meier. MIT License.
"""Das Vokabular muss wirken: richtige Schreibweise nach dem Diktat, ohne normale Wörter zu verfälschen.

Ausgangsfall: "Thorben" stand im Vokabular, die App schrieb trotzdem "Torben" – und lernte
die falsche Schreibweise nach jedem Diktat wieder dazu.
"""

import pytest

from services import vocabulary_service as v


@pytest.fixture(autouse=True)
def sandbox(monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path))


def vocab(*terms):
    v.save_user_list(list(terms))


# ── Der Ausgangsfall ────────────────────────────────────────────────────────

def test_falsch_erkannter_name_wird_auf_die_vokabel_schreibweise_gebracht():
    vocab("Thorben")
    assert v.apply("Hier ist Torben. Ich habe mit Torben gesprochen.") == \
        "Hier ist Thorben. Ich habe mit Thorben gesprochen."


def test_genitiv_und_apostroph_bleiben_erhalten():
    vocab("Thorben")
    assert v.apply("Das ist Torbens Laptop und Torben's Maus.") == "Das ist Thorbens Laptop und Thorben's Maus."


def test_auto_lernen_nimmt_die_falsche_schreibweise_nicht_wieder_auf():
    vocab("Thorben")
    v.add_terms(["Torben", "torben", "Petersen"])
    assert v.get_learned_terms() == ["Thorben", "Petersen"]


def test_loeschen_der_falschen_schreibweise_macht_daraus_eine_korrektur():
    """So sah die Liste des Nutzers aus: beide Schreibweisen. Er löscht die falsche."""
    v._write(v._vocab_path(), ["Surface", "Thorben", "Torben"])
    assert v.apply("Torben") == "Torben"                          # beide gewollt? Dann nicht raten.
    v.save_user_list(["Surface", "Thorben"])
    assert v.get_corrections() == {"torben": "Thorben"}
    assert v.apply("torben und Torben") == "Thorben und Thorben"
    v.add_terms(["Torben"])
    assert "Torben" not in v.get_learned_terms()


def test_nur_eine_schreibweise_geht_als_hinweis_an_die_spracherkennung():
    """Gemessen: Stehen Thorben UND Torben im Hinweis, schreibt Whisper "Torben"."""
    assert v.prompt_terms(["Thorben", "Torben", "Surface", "thorben"]) == ["Thorben", "Surface"]


def test_bekannte_fehlschreibung_geht_nie_als_hinweis_mit():
    v.save_user_list(["Carstens -> Karstens"])
    assert v.prompt_terms(["Carstens", "Karstens"]) == ["Karstens"]


def test_hinweis_ist_auf_eine_lesbare_laenge_begrenzt():
    many = [f"Begriff{i:03d}" for i in range(300)]
    hints = v.prompt_terms(many)
    assert hints[0] == "Begriff000" and len(hints) <= v.PROMPT_MAX_TERMS
    assert len(", ".join(hints)) <= v.PROMPT_MAX_CHARS


# ── Enge Regeln: Namen ja, normale Wörter nein ──────────────────────────────

@pytest.mark.parametrize("term, heard, expected", [
    ("Thomas", "Tomas ist da", "Thomas ist da"),
    ("Meier", "Herr Meyer kommt", "Herr Meier kommt"),
    ("Karstens", "Firma Carstens", "Firma Karstens"),
    ("Stephan", "mit Stefan", "mit Stephan"),
    ("Kathrin", "Frau Katrin", "Frau Kathrin"),
])
def test_namensvarianten_werden_angeglichen(term, heard, expected):
    vocab(term)
    assert v.apply(heard) == expected


@pytest.mark.parametrize("term, text", [
    ("Kahn", "Das kann ich"),                 # Fund der Durchsicht: wurde zu "Das Kahn ich"
    ("Mitte", "Die Miete ist fällig"),
    ("Ofen", "Das Fenster ist offen"),
    ("Stadt", "statt dessen"),
    ("Meer", "Wir brauchen mehr Zeit"),
    ("Thor", "Das Tor ist zu"),               # zu kurz für eine Angleichung
    ("Roth", "Rot ist die Farbe"),
    ("Project", "Das Projekt läuft lokal"),   # englischer Produktname darf deutsche Wörter nicht ändern
    ("Maße", "Die Masse ist geerdet"),
    ("Thorben", "torben ist kein Satzanfang"),  # klein geschrieben: kein Name
])
def test_normale_woerter_bleiben_unveraendert(term, text):
    vocab(term)
    assert v.apply(text) == text


def test_zwei_gewollte_schreibweisen_werden_nicht_geraten():
    vocab("Meier", "Meyer")
    assert v.apply("Herr Meier und Frau Meyer") == "Herr Meier und Frau Meyer"


def test_begriff_ohne_buchstaben_richtet_keinen_schaden_an():
    vocab("-", "…", "Thorben")
    assert v.apply("Hallo, Welt. Ja!") == "Hallo, Welt. Ja!"


def test_leeres_vokabular_aendert_nichts():
    assert v.apply("Torben Meyer") == "Torben Meyer"
    assert v.apply("") == ""


# ── Mehrteilige Begriffe und eigene Ersetzungen ─────────────────────────────

def test_mehrteilige_begriffe_werden_vereinheitlicht():
    vocab("Online-KI", "E-Mail")
    assert v.apply("Die online KI schreibt eine Email.") == "Die Online-KI schreibt eine E-Mail."


def test_eigene_ersetzung_mit_pfeil():
    count, fixes = v.save_user_list(["Karst Enz -> Karstens", "Blitz Diktat → Blitzdiktat", "Surface"])
    assert (count, fixes) == (3, 2)
    assert v.get_learned_terms() == ["Karstens", "Blitzdiktat", "Surface"]
    assert v.apply("Firma Karst Enz nutzt Blitz Diktat") == "Firma Karstens nutzt Blitzdiktat"


def test_ersetzung_mit_sonderzeichen_im_ziel():
    v.save_user_list([r"Pfad -> C:\1\g<0>"])
    assert v.apply("Der Pfad stimmt") == r"Der C:\1\g<0> stimmt"


def test_liste_zeigt_korrekturen_zum_bearbeiten_an():
    v.save_user_list(["Thorben", "Torben -> Thorben"])
    assert v.user_lines() == ["Thorben", "torben -> Thorben"]
    v.save_user_list(v.user_lines())                              # unverändert speichern
    assert v.get_corrections() == {"torben": "Thorben"}


def test_korrektur_verschwindet_wenn_der_begriff_geloescht_wird():
    v.save_user_list(["Thorben", "Torben -> Thorben"])
    v.save_user_list(["Surface"])
    assert v.get_corrections() == {}


def test_falsche_form_bewusst_als_begriff_eingetragen_hebt_die_korrektur_auf():
    v.save_user_list(["Thorben", "Torben -> Thorben"])
    v.save_user_list(["Thorben", "Torben"])                       # der Nutzer will beide
    assert v.get_corrections() == {}
    assert v.apply("Torben") == "Torben"


def test_alles_loeschen_entfernt_auch_die_korrekturen():
    v.save_user_list(["Thorben", "Torben -> Thorben"])
    v.clear()
    assert v.get_learned_terms() == [] and v.get_corrections() == {}


def test_kaputte_dateien_stoeren_nicht(tmp_path):
    with open(v._vocab_path(), "w", encoding="utf-8") as f:
        f.write("{kaputt")
    with open(v._corrections_path(), "w", encoding="utf-8") as f:
        f.write('["keine", "zuordnung"]')
    assert v.get_learned_terms() == [] and v.get_corrections() == {}
    assert v.apply("Text bleibt") == "Text bleibt"


# ── Im Ablauf ───────────────────────────────────────────────────────────────

def test_alle_workflows_bekommen_das_gelernte_vokabular():
    from types import SimpleNamespace
    from features.workflows.dampf_ablassen_workflow import DampfAblassenWorkflow
    from features.workflows.emoji_text_workflow import EmojiTextWorkflow
    from features.workflows.text_improvement_workflow import TextImprovementWorkflow
    for cls in (TextImprovementWorkflow, DampfAblassenWorkflow, EmojiTextWorkflow):
        wf = cls(SimpleNamespace(custom_terms=["nur-manuell"]), custom_terms=["Thorben"])
        assert wf._transcribe_terms() == ["Thorben"]


def test_korrektur_greift_vor_und_nach_der_verarbeitung(monkeypatch, tmp_path):
    from features.workflows import recording_workflow as rw
    from features.workflows.base_workflow import WorkflowType
    vocab("Thorben")
    seen: list[str] = []

    class Wf(rw.RecordingWorkflow):
        def _process(self, raw):
            seen.append(raw)
            return raw + " Gruß, Torben"                          # die KI schreibt es wieder falsch

    monkeypatch.setattr(rw, "transcribe_sync", lambda *a, **k: ("Hier ist Torben.", ""))
    wf = Wf(WorkflowType.TEXT_IMPROVER, custom_terms=[])
    wf._recorder = type("R", (), {"recording_path": "x.wav", "error_message": "", "discard_recording": lambda s: None})()
    out: list[str] = []
    wf.on_output = out.append
    wf._run()
    assert seen == ["Hier ist Thorben."]                          # die KI sieht schon den richtigen Namen
    assert out == ["Hier ist Thorben. Gruß, Thorben"]
