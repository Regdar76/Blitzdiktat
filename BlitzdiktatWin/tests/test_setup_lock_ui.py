# Copyright (c) 2026 Thorben Meier. MIT License.
"""Solange die Einrichtung läuft, ist Blitzdiktat gesperrt – und das ist sichtbar."""

from types import SimpleNamespace

import pytest

import app_state
from features.workflows.base_workflow import WorkflowType
from services import credentials_service, llm_service, local_ai_setup as las, paste_service

ctk = pytest.importorskip("customtkinter")


@pytest.fixture(autouse=True)
def sandbox(monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path / "roaming"))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    monkeypatch.setattr(credentials_service, "load_api_key", lambda: None)
    monkeypatch.setattr(credentials_service, "load_custom_api_key", lambda: None)
    monkeypatch.setattr(paste_service, "start_foreground_tracker", lambda: None)
    monkeypatch.setattr(llm_service, "list_models", lambda *a, **k: [])
    las.status.state, las.status.message, las.status.progress = las.IDLE, "", None
    yield
    las.status.state, las.status.message, las.status.progress = las.IDLE, "", None
    las._listeners.clear()


@pytest.fixture
def main_window():
    from features.ui.main_window import MainWindow
    try:
        mw = MainWindow(app_state.AppState())
    except Exception as e:
        pytest.skip(f"keine Oberfläche: {e}")
    yield mw
    mw._root.destroy()


def tiles_state(mw) -> set[str]:
    return {btn.cget("state") for btn in mw._wf_buttons.values()}


def test_hauptfenster_zeigt_ladeansicht_und_sperrt_die_kacheln(main_window):
    mw = main_window
    las._set(las.WORKING, "Lade LM Studio … 120 von 654 MB", 0.18)
    mw._refresh_setup_overlay()
    mw._root.update()
    assert mw._setup_visible and mw._setup_overlay.winfo_manager() == "place"
    assert "654 MB" in mw._setup_msg.cget("text")
    assert mw._setup_bar_mode == "determinate"                    # Fortschritt bekannt: echter Balken
    assert tiles_state(mw) == {"disabled"}
    assert "Einrichtung läuft" in mw._status_label.cget("text")


def test_ohne_bekannten_fortschritt_laeuft_der_balken_unbestimmt(main_window):
    mw = main_window
    las._set(las.WORKING, "Starte die lokale KI …")
    mw._refresh_setup_overlay()
    assert mw._setup_bar_mode == "indeterminate"


def test_nach_der_einrichtung_verschwindet_die_ladeansicht(main_window):
    mw = main_window
    las._set(las.WORKING, "Lade Gemma 4 E4B …", 0.5)
    mw._refresh_setup_overlay()
    las._set(las.READY, "Lokale KI bereit: Gemma 4 E4B")
    mw._refresh_setup_overlay()
    mw._root.update()
    assert not mw._setup_visible and mw._setup_overlay.winfo_manager() == ""
    assert tiles_state(mw) == {"normal"}


def test_ein_fehler_gibt_die_app_wieder_frei_und_meldet_ihn(main_window):
    mw = main_window
    las._set(las.WORKING, "Lade LM Studio …")
    mw._refresh_setup_overlay()
    las._set(las.FAILED, "keine Internetverbindung")
    mw._refresh_setup_overlay()
    assert not mw._setup_visible and tiles_state(mw) == {"normal"}
    assert "keine Internetverbindung" in mw._status_label.cget("text")


def test_ladeansicht_erscheint_auch_ohne_zustandsmeldung(main_window):
    """Das regelmäßige Nachsehen genügt: auch wenn kein Ereignis kommt, sperrt das Fenster."""
    mw = main_window
    las._set(las.WORKING, "Prüfe die Hardware …")
    mw._poll_setup()
    assert mw._setup_visible


def test_notiz_fenster_diktiert_nicht_waehrend_der_einrichtung(main_window):
    from features.ui.notiz_window import NotizWindow
    state = SimpleNamespace(
        settings=app_state.AppSettings(), active_workflow=None,
        setup_busy=lambda: "Lade Gemma 4 E4B …",
        capture_target_window=lambda: pytest.fail("darf nicht starten"),
        start_workflow=lambda t: pytest.fail("darf nicht starten"),
    )
    win = NotizWindow(main_window._root, state)
    try:
        win._toggle_dictation()
        assert "richtet sich noch ein" in win._status.cget("text")
    finally:
        win.destroy()


def test_einstellungen_sind_waehrend_der_einrichtung_gesperrt(main_window):
    from features.ui.settings_window import SettingsWindow
    app = main_window._app
    app.settings.llm_provider = "custom"
    win = SettingsWindow(main_window._root, app)
    try:
        win._toggle_advanced()                                    # Erweitert ist offen …
        assert win._adv_open
        las._set(las.WORKING, "Lade LM Studio …", 0.3)
        win._tick_auto_status()                                   # … und wird gesperrt
        assert not win._adv_open
        assert win._auto_btn.cget("state") == "disabled" and win._adv_toggle.cget("state") == "disabled"
        assert "Lade LM Studio" in win._auto_status.cget("text")
        las._set(las.READY, "Lokale KI bereit: Gemma 4 E4B")
        win._tick_auto_status()
        assert win._auto_btn.cget("state") == "normal" and win._adv_toggle.cget("state") == "normal"
    finally:
        win.destroy()
