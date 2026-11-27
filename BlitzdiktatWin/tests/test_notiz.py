# Copyright (c) 2026 Thorben Meier. MIT License.
"""Blitzdiktat Notiz: Entwurf, Export, Ablauf im Programm und das Notiz-Fenster."""

import asyncio
from types import SimpleNamespace

import pytest

import app_state
from features.workflows.base_workflow import WorkflowPhase, WorkflowType
from features.workflows.notiz_workflow import NotizWorkflow
from services import llm_service, note_service, paste_service


@pytest.fixture(autouse=True)
def sandbox(monkeypatch, tmp_path):
    """Entwurf, Einstellungen und Zwischenablage des echten Rechners bleiben unberührt."""
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    monkeypatch.setenv("APPDATA", str(tmp_path / "roaming"))
    monkeypatch.setattr(paste_service, "copy_to_clipboard", lambda text: pytest.fail("Test setzt eigene Attrappe"))


# ── Entwurf und Export ──────────────────────────────────────────────────────

def test_entwurf_wird_gesichert_und_geladen():
    assert note_service.load_draft() == ""
    note_service.save_draft("Guten Tag, äöü")
    assert note_service.load_draft() == "Guten Tag, äöü"


def test_leerer_text_loescht_den_entwurf():
    note_service.save_draft("etwas")
    note_service.save_draft("  \n ")
    assert note_service.load_draft() == ""


@pytest.mark.parametrize("existing, new, expected", [
    ("", "Hallo", "Hallo"),
    ("Hallo", "Welt", "Hallo Welt"),
    ("Hallo\n", "Welt", "Hallo\nWelt"),
    ("Hallo", "  ", "Hallo"),
])
def test_diktat_wird_passend_angehaengt(existing, new, expected):
    assert note_service.join_dictation(existing, new) == expected


def test_textexport_ist_fuer_word_und_editor_lesbar(tmp_path):
    path = tmp_path / "n.txt"
    note_service.export_text(str(path), "Grüße\nZeile 2")
    raw = path.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")                       # UTF-8 mit Kennung
    assert raw.decode("utf-8-sig") == "Grüße\r\nZeile 2"


def test_pdfexport_erzeugt_ein_pdf_auch_mit_sonderzeichen(tmp_path):
    pytest.importorskip("reportlab")
    path = tmp_path / "n.pdf"
    assert note_service.export_pdf(str(path), "A & B <b>\n\nZweiter Absatz äöü") is True
    assert path.read_bytes().startswith(b"%PDF")


def test_dateiname_vorschlag():
    name = note_service.suggested_filename("pdf")
    assert name.startswith("Notiz_") and name.endswith(".pdf")


# ── Ablauf im Programm ──────────────────────────────────────────────────────

def test_notiz_ist_ein_eigener_workflow():
    wf = NotizWorkflow()
    assert wf.workflow_type == WorkflowType.NOTIZ
    assert wf.PROCESS_STATUS is None                              # braucht keine Text-KI
    assert "\n" in wf._process("erster Punkt Absatz zweiter Punkt")
    assert WorkflowType.NOTIZ.display_name == "Blitzdiktat Notiz"


def _state():
    return app_state.AppState()


def test_tastenkuerzel_wird_gespeichert():
    s = app_state.AppSettings()
    assert s.hotkey_notiz == "ctrl+shift+n"
    s.hotkey_notiz = "ctrl+alt+n"
    app_state._save_settings(s)
    assert app_state._load_settings().hotkey_notiz == "ctrl+alt+n"


def test_diktierte_notiz_geht_ins_fenster_nicht_ins_zielfenster(monkeypatch):
    state = _state()
    got: list[str] = []
    saved: list[str] = []
    monkeypatch.setattr(paste_service, "paste_to_window", lambda hwnd, text: pytest.fail("darf nicht einfügen"))
    monkeypatch.setattr(app_state, "save_transcript", lambda text, name="": saved.append(text))
    monkeypatch.setattr(state, "_extract_vocabulary_bg", lambda text: pytest.fail("keine KI nötig"))
    state.note_listener = got.append
    wf = NotizWorkflow()
    state.active_workflow = wf
    state._on_workflow_output(wf, "Hallo Notiz")
    import time
    time.sleep(0.2)                                               # Speichern läuft im Thread
    assert got == ["Hallo Notiz"] and saved == ["Hallo Notiz"]


def test_andere_workflows_fuegen_weiter_ein(monkeypatch):
    from features.workflows.transcription_workflow import TranscriptionWorkflow
    state = _state()
    pasted: list[str] = []
    monkeypatch.setattr(paste_service, "paste_to_window", lambda hwnd, text: pasted.append(text))
    monkeypatch.setattr(app_state, "save_transcript", lambda text, name="": "")
    monkeypatch.setattr(llm_service, "is_available", lambda: False)
    state.note_listener = lambda text: pytest.fail("gehört nicht in die Notiz")
    wf = TranscriptionWorkflow()
    state.active_workflow = wf
    state._on_workflow_output(wf, "Normal")
    import time
    time.sleep(0.2)
    assert pasted == ["Normal"]


def test_notiz_startet_ohne_text_ki(monkeypatch):
    state = _state()
    monkeypatch.setattr(app_state.AppState, "is_configured", property(lambda self: True))
    monkeypatch.setattr(llm_service, "config_problem", lambda: pytest.fail("Notiz braucht keine Text-KI"))
    started: list[WorkflowType] = []
    monkeypatch.setattr(NotizWorkflow, "start", lambda self: started.append(self.workflow_type))
    state.start_workflow(WorkflowType.NOTIZ)
    assert started == [WorkflowType.NOTIZ]
    assert state.active_workflow.workflow_type == WorkflowType.NOTIZ


# ── Notiz-Fenster ───────────────────────────────────────────────────────────

ctk = pytest.importorskip("customtkinter")


@pytest.fixture
def root():
    try:
        r = ctk.CTk()
    except Exception as e:
        pytest.skip(f"keine Oberfläche: {e}")
    r.withdraw()
    yield r
    r.destroy()


@pytest.fixture
def clip(monkeypatch):
    copied: list[str] = []
    monkeypatch.setattr(paste_service, "copy_to_clipboard", copied.append)
    return copied


@pytest.fixture
def win(root, monkeypatch):
    from features.ui.notiz_window import NotizWindow
    monkeypatch.setattr(llm_service, "config_problem", lambda: None)
    state = SimpleNamespace(
        settings=app_state.AppSettings(), active_workflow=None,
        capture_target_window=lambda: None, start_workflow=lambda t: None, stop_workflow=lambda: None,
    )
    w = NotizWindow(root, state)
    w.state_stub = state
    yield w
    w.destroy()


def wait_idle(root, win, seconds=5):
    import time
    end = time.time() + seconds
    while win._busy and time.time() < end:
        root.update()
        time.sleep(0.03)
    root.update()


def test_entwurf_kommt_beim_oeffnen_zurueck(root, monkeypatch):
    from features.ui.notiz_window import NotizWindow
    note_service.save_draft("Alter Entwurf")
    state = SimpleNamespace(settings=app_state.AppSettings(), active_workflow=None)
    w = NotizWindow(root, state)
    try:
        assert w.get_text() == "Alter Entwurf"
    finally:
        w.destroy()


def test_diktat_wird_angehaengt_und_gesichert(root, win):
    win.set_text("Erster Satz.")
    win.append_dictation("Zweiter Satz.")
    assert win.get_text() == "Erster Satz. Zweiter Satz."
    win._flush_save()
    assert note_service.load_draft() == "Erster Satz. Zweiter Satz."


def test_text_aus_der_zwischenablage_einfuegen(root, win, monkeypatch):
    monkeypatch.setattr(win, "_clipboard_text", lambda: "Fremder Text")
    win._paste_clipboard()
    assert win.get_text() == "Fremder Text"                        # leeres Feld: ersetzen
    win._text.mark_set("insert", "end-1c")
    monkeypatch.setattr(win, "_clipboard_text", lambda: " Mehr.")
    win._paste_clipboard()
    assert win.get_text() == "Fremder Text Mehr."                 # sonst an der Schreibmarke


def test_leere_zwischenablage_aendert_nichts(root, win, monkeypatch):
    win.set_text("bleibt")
    monkeypatch.setattr(win, "_clipboard_text", lambda: "  ")
    win._paste_clipboard()
    assert win.get_text() == "bleibt"


def test_verbessern_wirkt_auf_den_ganzen_text_und_laesst_sich_zuruecknehmen(root, win, monkeypatch):
    async def fake_improve(text, settings):
        return text.upper()

    monkeypatch.setattr(llm_service, "improve", fake_improve)
    win.set_text("hallo welt")
    win._transform("improve")
    wait_idle(root, win)
    assert win.get_text() == "HALLO WELT"
    win._undo()
    assert win.get_text() == "hallo welt"


def test_ueberarbeiten_wirkt_nur_auf_die_markierung(root, win, monkeypatch):
    async def fake_calm(text, prompt=""):
        return "ruhig"

    monkeypatch.setattr(llm_service, "dampf_ablassen", fake_calm)
    win.set_text("Das ist unfassbar. Danke und Gruß.")
    win._text.tag_add("sel", "1.0", "1.18")                       # "Das ist unfassbar."
    win._transform("calm")
    wait_idle(root, win)
    assert win.get_text() == "ruhig Danke und Gruß."


def test_emojis_nutzen_die_eingestellte_dichte(root, win, monkeypatch):
    seen: list[str] = []

    async def fake_emoji(text, density):
        seen.append(density)
        return text + " 😊"

    monkeypatch.setattr(llm_service, "add_emojis", fake_emoji)
    win.state_stub.settings.emoji_text.emoji_density = "viel"
    win.set_text("Guten Morgen")
    win._transform("emoji")
    wait_idle(root, win)
    assert win.get_text() == "Guten Morgen 😊" and seen == ["viel"]


def test_fehler_der_ki_wird_gemeldet_und_der_text_bleibt(root, win, monkeypatch):
    async def broken(text, settings):
        raise RuntimeError("Server weg")

    monkeypatch.setattr(llm_service, "improve", broken)
    win.set_text("Text")
    win._transform("improve")
    wait_idle(root, win)
    assert win.get_text() == "Text"
    assert "Server weg" in win._status.cget("text")


def test_ohne_eingerichtete_ki_wird_nicht_ueberarbeitet(root, win, monkeypatch):
    monkeypatch.setattr(llm_service, "config_problem", lambda: "API Key fehlt — Einstellungen öffnen")
    monkeypatch.setattr(llm_service, "improve", lambda *a: pytest.fail("darf nicht aufrufen"))
    win.set_text("Text")
    win._transform("improve")
    assert "API Key fehlt" in win._status.cget("text") and not win._busy


def test_leerer_text_wird_nicht_ueberarbeitet(root, win, monkeypatch):
    monkeypatch.setattr(llm_service, "improve", lambda *a: pytest.fail("darf nicht aufrufen"))
    win._transform("improve")
    assert "Erst Text" in win._status.cget("text")


def test_kopieren_nimmt_markierung_sonst_alles(root, win, clip):
    win.set_text("Eins Zwei")
    win._copy()
    win._text.tag_add("sel", "1.0", "1.4")
    win._copy()
    assert clip == ["Eins Zwei", "Eins"]


def test_leere_notiz_wird_nicht_kopiert(root, win, clip):
    win._copy()
    assert clip == [] and "Kein Text" in win._status.cget("text")


def test_neue_notiz_laesst_sich_zuruecknehmen(root, win):
    win.set_text("Wichtiger Text")
    win._new_note()
    assert win.get_text() == ""
    win._undo()
    assert win.get_text() == "Wichtiger Text"


def test_export_als_textdatei(root, win, monkeypatch, tmp_path):
    from features.ui import notiz_window
    target = tmp_path / "out.txt"
    monkeypatch.setattr(notiz_window.filedialog, "asksaveasfilename", lambda **k: str(target))
    win.set_text("Für die Mail")
    win._export("txt")
    assert target.read_bytes().decode("utf-8-sig") == "Für die Mail"
    assert "Gespeichert" in win._status.cget("text")


def test_export_abgebrochen_schreibt_nichts(root, win, monkeypatch, tmp_path):
    from features.ui import notiz_window
    monkeypatch.setattr(notiz_window.filedialog, "asksaveasfilename", lambda **k: "")
    win.set_text("Text")
    win._export("pdf")
    assert list(tmp_path.glob("*.pdf")) == []


def test_aufnahme_zeigt_stopp_knopf(root, win):
    wf = SimpleNamespace(
        workflow_type=WorkflowType.NOTIZ, is_recording=True,
        state=SimpleNamespace(phase=WorkflowPhase.RECORDING, status_text="Aufnahme läuft ...", error_text=""),
    )
    win.state_stub.active_workflow = wf
    win.refresh()
    assert "Stopp" in win._dictate_btn.cget("text")
    wf.state.phase = WorkflowPhase.IDLE
    win.state_stub.active_workflow = None
    win.set_text("Schon Text da")
    assert "Weiter diktieren" in win._dictate_btn.cget("text")


def test_diktierknopf_startet_und_stoppt(root, win):
    calls: list[str] = []
    win.state_stub.start_workflow = lambda t: calls.append(f"start {t.value}")
    win.state_stub.stop_workflow = lambda: calls.append("stop")
    win._toggle_dictation()
    win.state_stub.active_workflow = SimpleNamespace(
        workflow_type=WorkflowType.NOTIZ, is_recording=True,
        state=SimpleNamespace(phase=WorkflowPhase.RECORDING, status_text="", error_text=""),
    )
    win._toggle_dictation()
    assert calls == ["start notiz", "stop"]
