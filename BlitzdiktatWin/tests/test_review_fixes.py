# Copyright (c) 2026 Thorben Meier. MIT License.
"""Korrekturen aus der Fehler- und Sicherheitsdurchsicht."""

import json
import os
import uuid
from types import SimpleNamespace

import pytest

import app_state
from features.workflows import recording_workflow as rw
from features.workflows.base_workflow import WorkflowPhase, WorkflowType
from services import (
    autostart_service, hardware_probe, local_ai_setup as las, local_server, paste_service, single_instance,
)


@pytest.fixture(autouse=True)
def sandbox(monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path / "roaming"))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    monkeypatch.setattr(app_state, "LOAD_PROBLEM", False)
    las.status.state, las.status.message, las.status.progress = las.IDLE, "", None


# ── Ein Diktat geht bei einem Fehler nicht mehr verloren ────────────────────

class _Recorder:
    recording_path = "x.wav"
    error_message = ""

    def __init__(self):
        self.discarded = False

    def discard_recording(self):
        self.discarded = True


def _failing_workflow(monkeypatch, transcript="Eine Stunde Besprechung."):
    saved: list[tuple[str, str]] = []
    monkeypatch.setattr(rw, "transcribe_sync", lambda *a, **k: (transcript, ""))
    monkeypatch.setattr(rw, "save_transcript", lambda text, name="": saved.append((text, name)))

    class Wf(rw.RecordingWorkflow):
        PROCESS_STATUS = "Wird verarbeitet ..."

        def _process(self, raw):
            raise RuntimeError("KI-Server antwortet nicht")

    wf = Wf(WorkflowType.PROTOKOLL, custom_terms=[])
    wf._recorder = _Recorder()
    return wf, saved


def test_scheitert_die_verarbeitung_bleibt_der_erkannte_text_erhalten(monkeypatch):
    wf, saved = _failing_workflow(monkeypatch)
    out: list[str] = []
    wf.on_output = out.append
    wf._run()
    assert wf.state.phase == WorkflowPhase.ERROR
    assert saved and saved[0][0] == "Eine Stunde Besprechung." and "Rohtext" in saved[0][1]
    assert "Rohtext gesichert" in wf.state.error_text
    assert out == []


def test_die_aufnahme_wird_bei_einem_fehler_nicht_mehr_geloescht(monkeypatch):
    wf, _ = _failing_workflow(monkeypatch)
    wf._run()
    assert wf._recorder.discarded is False


def test_scheitert_schon_die_erkennung_gibt_es_keinen_rohtext(monkeypatch):
    saved: list[str] = []
    monkeypatch.setattr(rw, "transcribe_sync", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("Mikrofon")))
    monkeypatch.setattr(rw, "save_transcript", lambda text, name="": saved.append(text))
    wf = rw.RecordingWorkflow(WorkflowType.TRANSCRIPTION, custom_terms=[])
    wf._recorder = _Recorder()
    wf._run()
    assert wf.state.phase == WorkflowPhase.ERROR and saved == []
    assert "Rohtext" not in wf.state.error_text


def _state(monkeypatch):
    state = app_state.AppState()
    monkeypatch.setattr(type(state), "is_configured", property(lambda self: True))
    return state


def test_neuer_start_zerstoert_kein_diktat_in_verarbeitung(monkeypatch):
    state = _state(monkeypatch)
    running = SimpleNamespace(
        workflow_type=WorkflowType.PROTOKOLL, state=SimpleNamespace(phase=WorkflowPhase.PROCESSING),
        cancel=lambda: pytest.fail("darf nicht abbrechen"), reset=lambda: pytest.fail("darf nicht zurücksetzen"),
    )
    state.active_workflow = running
    for wtype in WorkflowType:
        state.start_workflow(wtype)
    assert state.active_workflow is running
    assert "wird noch verarbeitet" in state.notification


def test_datei_import_zerstoert_kein_diktat_in_verarbeitung(monkeypatch):
    state = _state(monkeypatch)
    running = SimpleNamespace(
        workflow_type=WorkflowType.PROTOKOLL, state=SimpleNamespace(phase=WorkflowPhase.PROCESSING),
        cancel=lambda: pytest.fail("darf nicht abbrechen"), reset=lambda: None,
    )
    state.active_workflow = running
    state.import_file_for_protokoll("x.txt")
    assert state.active_workflow is running


# ── Einstellungen ───────────────────────────────────────────────────────────

def test_kaputte_einstellungen_werden_aufgehoben_statt_ueberschrieben():
    path = app_state._settings_path()
    with open(path, "w", encoding="utf-8") as f:
        f.write('{"hotkey_transcription": "ctrl+alt+r",}')          # Komma zu viel
    s = app_state._load_settings()
    assert s.hotkey_transcription == "ctrl+shift+r"                # Standard
    assert app_state.LOAD_PROBLEM is True
    assert "ctrl+alt+r" in open(path + ".defekt", encoding="utf-8").read()
    assert not os.path.exists(path)


def test_null_statt_liste_legt_die_tastenkuerzel_nicht_lahm():
    with open(app_state._settings_path(), "w", encoding="utf-8") as f:
        json.dump({"text_improvement": {"custom_terms": None}, "dampf_ablassen": None, "protokoll": None}, f)
    s = app_state._load_settings()
    assert s.text_improvement.custom_terms == [] and app_state.LOAD_PROBLEM is False
    assert s.dampf_ablassen.system_prompt == ""


def test_speichern_hinterlaesst_keine_halbe_datei(monkeypatch):
    s = app_state.AppSettings()
    s.hotkey_notiz = "ctrl+alt+n"
    app_state._save_settings(s)
    path = app_state._settings_path()
    assert not os.path.exists(path + ".tmp")
    assert json.load(open(path, encoding="utf-8"))["hotkey_notiz"] == "ctrl+alt+n"

    # Scheitert das Schreiben, bleibt die alte Datei unversehrt.
    monkeypatch.setattr(app_state.json, "dump", lambda *a, **k: (_ for _ in ()).throw(OSError("Platte voll")))
    s.hotkey_notiz = "kaputt"
    app_state._save_settings(s)
    monkeypatch.undo()
    assert json.load(open(path, encoding="utf-8"))["hotkey_notiz"] == "ctrl+alt+n"


# ── Nur eine Instanz ────────────────────────────────────────────────────────

def test_zweiter_start_wird_erkannt_und_weckt_die_erste_instanz():
    import threading
    tag = uuid.uuid4().hex
    mutex, event = f"Local\\Blitzdiktat-Test-{tag}", f"Local\\Blitzdiktat-Test-Zeigen-{tag}"
    shown = threading.Event()
    assert single_instance.acquire(mutex, event) is True
    single_instance.on_second_start(shown.set, event)
    assert single_instance.acquire(mutex, event) is False          # zweiter Start
    assert shown.wait(3), "die erste Instanz wurde nicht gebeten, ihr Fenster zu zeigen"


# ── Autostart ───────────────────────────────────────────────────────────────

@pytest.fixture
def run_key(monkeypatch):
    import winreg
    key = rf"Software\Blitzdiktat-Test-{uuid.uuid4().hex}"
    monkeypatch.setattr(autostart_service, "RUN_KEY", key)
    yield key
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key)
    except OSError:
        pass


def test_autostart_ein_und_ausschalten(run_key, monkeypatch):
    monkeypatch.setattr(autostart_service.sys, "executable", r"C:\Program Files\Blitzdiktat\Blitzdiktat.exe")
    assert autostart_service.is_enabled() is False
    assert autostart_service.set_enabled(True) and autostart_service.is_enabled()
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, run_key) as k:
        value = winreg.QueryValueEx(k, autostart_service.VALUE_NAME)[0]
    assert value == r'"C:\Program Files\Blitzdiktat\Blitzdiktat.exe"'      # Pfad mit Leerzeichen in Anführungszeichen
    assert autostart_service.set_enabled(False) and not autostart_service.is_enabled()
    assert autostart_service.set_enabled(False)                    # doppelt ausschalten ist kein Fehler


def test_autostart_nur_im_installierten_programm():
    assert autostart_service.is_supported() is False                # Tests laufen aus dem Quellcode


# ── Automatische Einrichtung: sicherer Download, kein Dauer-Neuversuch ──────

def _install_env(monkeypatch, tmp_path, returncode=0, tamper=False):
    import hashlib
    data = b"setup-inhalt"
    monkeypatch.setattr(las, "LM_STUDIO_SHA256", hashlib.sha256(data).hexdigest())
    monkeypatch.setattr(las, "_free_gb", lambda p: 500)
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setattr(os.path, "expanduser", lambda p: str(tmp_path) if p == "~" else p)
    state = {"installed": False, "ran": []}

    def fake_download(url, dest, sha, size, progress):
        with open(dest, "wb") as f:
            f.write(b"ausgetauscht" if tamper else data)

    def fake_run(cmd, **kw):
        state["ran"].append(cmd[0])
        assert os.path.dirname(cmd[0]) != las.tempfile.gettempdir()        # eigener Ordner, kein fester Name in %TEMP%
        state["installed"] = returncode == 0
        return SimpleNamespace(returncode=returncode)

    monkeypatch.setattr(las, "_download_file", fake_download)
    monkeypatch.setattr(las.subprocess, "run", fake_run)
    monkeypatch.setattr(local_server, "find_app", lambda: "LM Studio.exe" if state["installed"] else None)
    return state


def test_ausgetauschte_datei_wird_vor_dem_start_erkannt(monkeypatch, tmp_path):
    state = _install_env(monkeypatch, tmp_path, tamper=True)
    with pytest.raises(las.SetupError, match="Prüfsumme"):
        las.install_lm_studio(lambda *a: None)
    assert state["ran"] == []                                       # nichts ausgeführt


def test_fehlercode_des_installers_wird_ernst_genommen(monkeypatch, tmp_path):
    _install_env(monkeypatch, tmp_path, returncode=2)
    with pytest.raises(las.SetupError, match="Fehlercode 2"):
        las.install_lm_studio(lambda *a: None)


def test_installationsdatei_wird_wieder_entfernt(monkeypatch, tmp_path):
    state = _install_env(monkeypatch, tmp_path)
    las.install_lm_studio(lambda *a: None)
    assert state["ran"] and not os.path.exists(state["ran"][0])


def test_datenordner_gehoert_nur_dann_uns_wenn_er_neu_ist(monkeypatch, tmp_path):
    _install_env(monkeypatch, tmp_path)
    las.install_lm_studio(lambda *a: None)
    flags = json.load(open(las.ownership_path(), encoding="utf-8"))
    assert flags == {"lmstudio": True, "gemma": False, "lmstudio_data": True}


def test_vorhandener_datenordner_wird_nie_als_unserer_vermerkt(monkeypatch, tmp_path):
    (tmp_path / ".lmstudio").mkdir()                                # der Nutzer hatte LM Studio schon einmal
    _install_env(monkeypatch, tmp_path)
    las.install_lm_studio(lambda *a: None)
    flags = json.load(open(las.ownership_path(), encoding="utf-8"))
    assert flags["lmstudio"] is True and flags["lmstudio_data"] is False


def test_merkdatei_passt_zum_setup():
    las.remember_ownership(lmstudio=True, lmstudio_data=True)
    text = open(las.ownership_path(), encoding="utf-8").read()
    # Das Setup sucht genau nach diesen Zeichenfolgen (Pascal: Pos('"flag": true', ...)).
    assert '"lmstudio": true' in text and '"lmstudio_data": true' in text and '"gemma": false' in text
    iss = open(os.path.join(os.path.dirname(__file__), "..", "installer_lokale_ki.iss"), encoding="utf-8-sig").read()
    assert "Owns('lmstudio_data')" in iss and '"lmstudio_data": ' in iss


def _settings():
    return SimpleNamespace(
        local_ai_auto=True, llm_provider="custom", custom_llm_base_url="http://localhost:1234/v1", custom_llm_model="",
    )


def test_nach_gescheiterter_installation_wird_nicht_bei_jedem_start_neu_geladen(monkeypatch):
    calls: list[int] = []
    monkeypatch.setattr(local_server, "find_app", lambda: None)

    def broken(progress):
        calls.append(1)
        raise las.SetupError("keine Internetverbindung")

    monkeypatch.setattr(las, "install_lm_studio", broken)
    las.run(_settings(), lambda: None)
    assert las.status.state == las.FAILED and calls == [1] and las.install_failed_recently()
    las.run(_settings(), lambda: None)                              # nächster Programmstart
    assert calls == [1] and "später" in las.status.message
    las.run(_settings(), lambda: None, force=True)                  # Knopf in den Einstellungen
    assert calls == [1, 1]


def test_nach_der_wartezeit_wird_wieder_versucht(monkeypatch):
    las._note_install_failure(True)
    with open(las._failure_path(), "w", encoding="utf-8") as f:
        json.dump({"time": 0}, f)                                   # lange her
    assert las.install_failed_recently() is False


# ── Keine Programme über den Suchpfad ───────────────────────────────────────

def test_lms_wird_nicht_ueber_den_suchpfad_gestartet(monkeypatch, tmp_path):
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))
    for var in ("LOCALAPPDATA", "ProgramFiles", "ProgramFiles(x86)"):
        monkeypatch.setenv(var, str(tmp_path / "leer"))
    monkeypatch.setattr(local_server.shutil, "which", lambda name: r"C:\fremd\lms.exe")
    assert local_server.find_lms() is None


def test_nvidia_smi_nur_mit_festem_pfad(monkeypatch, tmp_path):
    monkeypatch.setenv("SystemRoot", str(tmp_path))
    called: list[list[str]] = []
    monkeypatch.setattr(hardware_probe, "_run", lambda args, timeout=20: called.append(args) or "")
    assert hardware_probe._gpus_from_nvidia_smi() == [] and called == []      # nicht vorhanden: gar nicht starten
    exe = tmp_path / "System32" / "nvidia-smi.exe"
    exe.parent.mkdir()
    exe.write_bytes(b"")
    hardware_probe._gpus_from_nvidia_smi()
    assert called and called[0][0] == str(exe)


# ── Einfügen ────────────────────────────────────────────────────────────────

def test_zeilenumbrueche_fuer_klassische_eingabefelder(monkeypatch):
    sent: list[str] = []

    class U:
        def SendMessageW(self, hctrl, msg, wparam, lparam):
            if msg == paste_service._EM_REPLACESEL:
                import ctypes
                sent.append(ctypes.wstring_at(lparam))
                return 0
            return len(sent)                                        # Textlänge wächst nach dem Einfügen

    monkeypatch.setattr(paste_service, "_user32", U())
    paste_service._insert_via_replacesel(1, "Zeile 1\nZeile 2\r\nZeile 3")
    assert sent == ["Zeile 1\r\nZeile 2\r\nZeile 3"]


def test_cloud_sperre_stoert_das_einfuegen_nie(monkeypatch):
    class Broken:
        def __getattr__(self, name):
            raise OSError("kein Zugriff")

    monkeypatch.setattr(paste_service, "_user32", Broken())
    paste_service._keep_out_of_cloud()                              # darf nicht werfen


# ── Tastenkürzel ────────────────────────────────────────────────────────────

@pytest.mark.parametrize("typed", ["ctrl+shift+r", "Strg+Umschalt+R", " ctrl + shift + r ", "STRG+SHIFT+r", "ctrl++shift+r"])
def test_tastenkuerzel_werden_verstanden_wie_getippt(typed):
    from services.hotkey_service import HotkeyService
    assert HotkeyService._parse(typed) == frozenset({"ctrl", "shift", "r"})
