# Copyright (c) 2026 Thorben Meier. MIT License.
"""Automatische Einrichtung der lokalen KI – ohne echtes LM Studio und ohne Downloads."""

import io
import json
import os
import re
import threading
from types import SimpleNamespace

import pytest

from services import (
    credentials_service, hardware_probe, llm_service, local_ai_pins, local_ai_setup as las,
    local_benchmark, local_server, model_catalog as mc,
)

REAL_INSTALL = las.install_lm_studio            # die Fixture ersetzt sie durch eine Attrappe

URL = "http://localhost:1234/v1"
GPU = hardware_probe.Hardware(ram_gb=32, cpu_threads=16, gpus=[hardware_probe.Gpu("Karte", 11)])      # → E4B
CPU = hardware_probe.Hardware(ram_gb=16, cpu_threads=8)                                              # → E2B
WEAK = hardware_probe.Hardware(ram_gb=8, cpu_threads=4)                                              # → nichts


class World:
    """Ein simuliertes LM Studio: was installiert ist, welche Modelle da sind, was geladen wurde."""

    def __init__(self):
        self.lm_studio = True
        self.server_ok = True
        self.server_reason = "kaputt"
        self.models = ["google/gemma-4-e2b"]
        self.download_ok = True
        self.calls: list[str] = []
        self.hw = GPU
        self.free_gb = 500.0
        self.loaded: list[str] = []


@pytest.fixture
def world(monkeypatch, tmp_path):
    w = World()
    monkeypatch.setenv("APPDATA", str(tmp_path / "roaming"))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setattr(credentials_service, "load_api_key", lambda: None)
    monkeypatch.setattr(credentials_service, "load_custom_api_key", lambda: None)
    monkeypatch.setattr(local_server, "find_lms", lambda: "lms.exe" if w.lm_studio else None)
    monkeypatch.setattr(local_server, "find_app", lambda: "LM Studio.exe" if w.lm_studio else None)

    def start(url, wait=90.0, force=False):
        w.calls.append("server")
        return local_server.StartResult(w.server_ok, "" if w.server_ok else w.server_reason)

    monkeypatch.setattr(local_server, "start_local_server", start)
    monkeypatch.setattr(local_server, "ensure_model_loaded", lambda url, m: w.loaded.append(m) or True)
    monkeypatch.setattr(hardware_probe, "detect", lambda: w.hw)
    monkeypatch.setattr(llm_service, "list_models", lambda *a, **k: list(w.models))
    monkeypatch.setattr(las, "_free_gb", lambda path: w.free_gb)

    def install(progress):
        w.calls.append("install_lm_studio")
        w.lm_studio = True

    monkeypatch.setattr(las, "install_lm_studio", install)

    def download(model, url, progress):
        w.calls.append(f"download {model.key}")
        if w.download_ok:
            w.models.append(model.key)
            return True, "ok"
        return False, "Netzwerk weg"

    monkeypatch.setattr(local_benchmark, "download", download)
    monkeypatch.setattr(las, "_partial_bytes", lambda: 0)
    las.status.state, las.status.message = las.IDLE, ""
    return w


def settings(**over):
    base = dict(
        local_ai_auto=True, llm_provider="custom", custom_llm_base_url=URL, custom_llm_model="google/gemma-4-e2b",
    )
    base.update(over)
    return SimpleNamespace(**base)


def run(s, force=False):
    saved: list[str] = []
    notes: list[str] = []
    las.run(s, lambda: saved.append(s.custom_llm_model), notes.append, force)
    return saved, notes


# ── Wann ist die Einrichtung nötig? ─────────────────────────────────────────

def test_automatik_aus_dann_nichts(world):
    assert not las.needs_local_ai(settings(local_ai_auto=False))


def test_fremder_server_wird_nie_eingerichtet(world):
    assert not las.needs_local_ai(settings(custom_llm_base_url="https://ki.firma.example/v1"))


def test_lokale_ki_gewaehlt_dann_ja(world):
    assert las.needs_local_ai(settings())


def test_online_mit_schluessel_bleibt_unberuehrt(world, monkeypatch):
    monkeypatch.setattr(credentials_service, "load_api_key", lambda: "sk-test")
    assert not las.needs_local_ai(settings(llm_provider="openai"))


def test_online_ohne_schluessel_nur_wenn_das_setup_die_ki_vorsah(world):
    s = settings(llm_provider="openai", custom_llm_model="")
    assert not las.needs_local_ai(s)
    las.remember_ownership()                                      # Merkdatei vom Setup
    assert las.needs_local_ai(s)


# ── Ablauf ──────────────────────────────────────────────────────────────────

def test_alles_bereit_nichts_zu_tun(world):
    world.models = ["google/gemma-4-e4b", "google/gemma-4-e2b"]
    s = settings(custom_llm_model="google/gemma-4-e4b")
    saved, notes = run(s)
    assert las.status.state == las.READY and "Gemma 4 E4B" in las.status.message
    assert not [c for c in world.calls if c.startswith(("download", "install"))]
    assert saved == [] and notes == []                            # nichts geändert, keine Meldung
    assert world.loaded == ["google/gemma-4-e4b"]


def test_fehlendes_zielmodell_wird_geladen_bis_dahin_arbeitet_das_vorhandene(world):
    s = settings()                                                # nutzt E2B, Ziel für GPU ist E4B
    saved, notes = run(s)
    assert world.calls == ["server", "download google/gemma-4-e4b"]
    assert s.custom_llm_model == "google/gemma-4-e4b" and las.status.state == las.READY
    assert notes == ["Lokale KI ist bereit: Gemma 4 E4B"]
    assert world.loaded[0] == "google/gemma-4-e2b" and world.loaded[-1] == "google/gemma-4-e4b"


def test_ohne_grafikkarte_bleibt_das_kleine_modell(world):
    world.hw = CPU
    saved, notes = run(settings())
    assert not [c for c in world.calls if c.startswith("download")]
    assert las.status.state == las.READY and "Gemma 4 E2B" in las.status.message


def test_lm_studio_fehlt_wird_installiert_dann_geht_es_weiter(world):
    world.lm_studio = False
    saved, notes = run(settings())
    assert world.calls[0] == "install_lm_studio" and "server" in world.calls
    assert las.status.state == las.READY


def test_nur_lms_im_profil_ohne_programm_gilt_als_nicht_installiert(world, monkeypatch):
    """Nach einer Deinstallation bleibt lms.exe liegen – LM Studio muss trotzdem neu installiert werden."""
    world.lm_studio = False
    monkeypatch.setattr(local_server, "find_lms", lambda: "lms.exe")
    run(settings())
    assert world.calls[0] == "install_lm_studio"


def test_lm_studio_installation_scheitert_meldung_an_den_nutzer(world, monkeypatch):
    world.lm_studio = False

    def broken(progress):
        raise las.SetupError("keine Internetverbindung")

    monkeypatch.setattr(las, "install_lm_studio", broken)
    saved, notes = run(settings())
    assert las.status.state == las.FAILED and "Internetverbindung" in las.status.message
    assert notes == ["Lokale KI konnte nicht eingerichtet werden: keine Internetverbindung"]


def test_server_startet_nicht(world):
    world.server_ok = False
    saved, notes = run(settings())
    assert las.status.state == las.FAILED and "kaputt" in las.status.message and len(notes) == 1


def test_download_scheitert_vorhandenes_modell_laeuft_weiter(world):
    world.download_ok = False
    s = settings()
    saved, notes = run(s)
    assert las.status.state == las.READY and "gescheitert" in las.status.message
    assert s.custom_llm_model == "google/gemma-4-e2b" and notes == []


def test_download_scheitert_ohne_vorhandenes_modell_ist_ein_fehler(world):
    world.download_ok = False
    world.models = []
    saved, notes = run(settings(custom_llm_model=""))
    assert las.status.state == las.FAILED and "Netzwerk weg" in las.status.message and len(notes) == 1


def test_erstes_modell_wird_geladen_und_aktiviert(world):
    world.models = []
    world.hw = CPU
    s = settings(llm_provider="openai", custom_llm_model="")
    las.remember_ownership()
    saved, notes = run(s)
    assert s.llm_provider == "custom" and s.custom_llm_model == "google/gemma-4-e2b"
    assert saved and notes == ["Lokale KI ist bereit: Gemma 4 E2B"]


def test_zu_wenig_speicherplatz_beim_ziel_behaelt_das_vorhandene(world):
    world.free_gb = 2
    s = settings()
    saved, notes = run(s)
    assert las.status.state == las.READY and "Speicherplatz" in las.status.message
    assert not [c for c in world.calls if c.startswith("download")]


def test_zu_schwacher_rechner_ohne_modell(world):
    world.hw = WEAK
    world.models = []
    saved, notes = run(settings(custom_llm_model=""))
    assert las.status.state == las.FAILED and "zu schwach" in las.status.message


def test_zu_schwacher_rechner_mit_vorhandenem_modell_nutzt_es(world):
    world.hw = WEAK
    saved, notes = run(settings())
    assert las.status.state == las.READY and "knapp" in las.status.message


def test_eigenes_modell_des_nutzers_wird_nicht_angefasst(world):
    world.models = ["mein/spezialmodell", "google/gemma-4-e2b"]
    s = settings(custom_llm_model="mein/spezialmodell")
    saved, notes = run(s)
    assert s.custom_llm_model == "mein/spezialmodell" and las.status.state == las.READY
    assert not [c for c in world.calls if c.startswith("download")]


def test_alter_modellname_wird_ueber_alias_erkannt(world):
    world.models = ["google/gemma-4-e2b"]
    world.hw = CPU
    s = settings(custom_llm_model="gemma-4-e2b-it")
    run(s)
    assert s.custom_llm_model == "google/gemma-4-e2b" and not [c for c in world.calls if c.startswith("download")]


def test_automatik_aus_fuehrt_nichts_aus(world):
    saved, notes = run(settings(local_ai_auto=False))
    assert world.calls == [] and las.status.state == las.NOT_NEEDED


def test_knopf_in_den_einstellungen_schaltet_die_automatik_wieder_ein(world):
    s = settings(local_ai_auto=False)
    run(s, force=True)
    assert s.local_ai_auto is True and las.status.state == las.READY


def test_zweiter_aufruf_waehrend_der_einrichtung_wird_ignoriert(world, monkeypatch):
    gate = threading.Event()
    release = threading.Event()

    def slow_download(model, url, progress):
        gate.set()
        release.wait(5)
        world.models.append(model.key)
        return True, "ok"

    monkeypatch.setattr(local_benchmark, "download", slow_download)
    t = threading.Thread(target=run, args=(settings(),))
    t.start()
    assert gate.wait(5)
    saved, notes = run(settings())                                # sofort zurück
    assert las.is_working()
    release.set()
    t.join(5)
    assert las.status.state == las.READY


def test_ohne_den_nutzer_keine_ausnahme_nach_aussen(world, monkeypatch):
    monkeypatch.setattr(hardware_probe, "detect", lambda: (_ for _ in ()).throw(RuntimeError("kaputt")))
    run(settings())
    assert las.status.state == las.FAILED and "Unerwarteter Fehler" in las.status.message


def test_statusmeldungen_gehen_an_die_zuhoerer(world):
    seen: list[str] = []
    las.subscribe(lambda st: seen.append(st.state))
    try:
        run(settings())
    finally:
        las._listeners.clear()
    assert las.WORKING in seen and seen[-1] == las.READY


# ── Merkdatei ───────────────────────────────────────────────────────────────

def test_merkdatei_hat_denselben_aufbau_wie_im_setup(world):
    las.remember_ownership(lmstudio=True)
    assert open(las.ownership_path(), encoding="utf-8").read() == '{"lmstudio": true, "gemma": false, "lmstudio_data": false}'
    las.remember_ownership(gemma=True)
    assert open(las.ownership_path(), encoding="utf-8").read() == '{"lmstudio": true, "gemma": true, "lmstudio_data": false}'


def test_merkdatei_behaelt_ein_frueheres_true(world):
    las.remember_ownership(lmstudio=True)
    las.remember_ownership()                                      # z. B. bei einem Update
    assert json.load(open(las.ownership_path(), encoding="utf-8"))["lmstudio"] is True


def test_merkdatei_aus_dem_setup_mit_bom_wird_gelesen(world):
    os.makedirs(os.path.dirname(las.ownership_path()), exist_ok=True)
    with open(las.ownership_path(), "wb") as f:
        f.write(b'\xef\xbb\xbf{"lmstudio": true, "gemma": false}')
    las.remember_ownership(gemma=True)
    assert json.load(open(las.ownership_path(), encoding="utf-8"))["lmstudio"] is True


# ── LM Studio laden und installieren ────────────────────────────────────────

class _Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


def test_pins_stimmen_mit_dem_setup_ueberein():
    iss = open(os.path.join(os.path.dirname(__file__), "..", "installer_lokale_ki.iss"), encoding="utf-8-sig").read()
    assert re.search(r'#define LMStudioVersion\s+"%s"' % re.escape(local_ai_pins.LM_STUDIO_VERSION), iss)
    assert re.search(r'#define LMStudioSha256\s+"%s"' % local_ai_pins.LM_STUDIO_SHA256, iss)
    assert re.search(r'#define LMStudioBytes\s+"%d"' % local_ai_pins.LM_STUDIO_BYTES, iss)
    assert local_ai_pins.LM_STUDIO_URL.startswith("https://installers.lmstudio.ai/")


def test_download_mit_richtiger_pruefsumme(tmp_path, monkeypatch):
    import hashlib
    data = b"x" * 1000
    monkeypatch.setattr(las.urllib.request, "urlopen", lambda req, timeout=0: _Response(data))
    dest = tmp_path / "setup.exe"
    las._download_file("https://example/x.exe", str(dest), hashlib.sha256(data).hexdigest(), 1000, lambda *a: None)
    assert dest.read_bytes() == data


def test_download_mit_falscher_pruefsumme_wird_verworfen(tmp_path, monkeypatch):
    monkeypatch.setattr(las.urllib.request, "urlopen", lambda req, timeout=0: _Response(b"boese"))
    dest = tmp_path / "setup.exe"
    with pytest.raises(las.SetupError, match="Prüfsumme"):
        las._download_file("https://example/x.exe", str(dest), "0" * 64, 5, lambda *a: None)
    assert not dest.exists()


def test_download_ohne_internet_gibt_klare_meldung(tmp_path, monkeypatch):
    def offline(req, timeout=0):
        raise OSError("getaddrinfo failed")

    monkeypatch.setattr(las.urllib.request, "urlopen", offline)
    with pytest.raises(las.SetupError, match="Internetverbindung"):
        las._download_file("https://example/x.exe", str(tmp_path / "s.exe"), "0" * 64, 5, lambda *a: None)


def test_installation_still_merkt_sich_und_entfernt_die_desktopverknuepfung(world, monkeypatch, tmp_path):
    state = {"installed": False}
    ran: list[list[str]] = []
    desktop = tmp_path / "Desktop"
    desktop.mkdir()
    (desktop / "LM Studio.lnk").write_bytes(b"")
    monkeypatch.setattr(las, "_free_gb", lambda p: 500)
    import hashlib
    monkeypatch.setattr(las, "LM_STUDIO_SHA256", hashlib.sha256(b"setup").hexdigest())
    monkeypatch.setattr(las, "_download_file", lambda url, dest, *a: open(dest, "wb").write(b"setup"))
    monkeypatch.setattr(local_server, "find_lms", lambda: "lms.exe")        # Rest der alten Installation
    monkeypatch.setattr(local_server, "find_app", lambda: "LM Studio.exe" if state["installed"] else None)
    monkeypatch.delenv("OneDrive", raising=False)

    def fake_run(cmd, **kw):
        ran.append(cmd)
        assert "/S" in cmd                                          # still
        assert kw["creationflags"] == getattr(las.subprocess, "CREATE_NO_WINDOW", 0)
        state["installed"] = True
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(las.subprocess, "run", fake_run)
    REAL_INSTALL(lambda *a: None)
    assert len(ran) == 1
    assert not (desktop / "LM Studio.lnk").exists()
    assert json.load(open(las.ownership_path(), encoding="utf-8"))["lmstudio"] is True


def test_installation_bricht_bei_zu_wenig_platz_ab(world, monkeypatch):
    monkeypatch.setattr(las, "_free_gb", lambda p: 1)
    monkeypatch.setattr(las, "_download_file", lambda *a: pytest.fail("darf nicht laden"))
    with pytest.raises(las.SetupError, match="Speicherplatz"):
        REAL_INSTALL(lambda *a: None)


# ── Sperre, solange die Einrichtung läuft ───────────────────────────────────

def test_fortschritt_wird_im_status_gemeldet(world, monkeypatch):
    seen: list[tuple[str, float | None]] = []
    las.subscribe(lambda st: seen.append((st.message, st.progress)))
    monkeypatch.setattr(las, "_partial_bytes", lambda: int(3 * 1024 ** 3))

    def slow_download(model, url, progress):
        import time
        time.sleep(2.2)                                           # der Fortschritt wird alle 2 s abgefragt
        world.models.append(model.key)
        return True, "ok"

    monkeypatch.setattr(local_benchmark, "download", slow_download)
    try:
        run(settings())
    finally:
        las._listeners.clear()
    downloads = [(m, p) for m, p in seen if m.startswith("Lade Gemma 4 E4B")]
    assert downloads and downloads[0][1] == pytest.approx(0.5, abs=0.05)      # 3 von 6 GB
    assert las.status.progress is None                            # fertig: kein Balken mehr


def test_ab_dem_start_gilt_die_einrichtung_als_laufend(world):
    las.mark_starting()
    assert las.is_working() and las.status.progress is None


def _app():
    import app_state
    return app_state.AppState()


def test_app_ist_gesperrt_solange_die_einrichtung_laeuft(world, monkeypatch):
    state = _app()
    las._set(las.WORKING, "Lade LM Studio … 120 von 654 MB", 0.18)
    assert state.setup_busy() == "Lade LM Studio … 120 von 654 MB"
    started: list[object] = []
    monkeypatch.setattr(type(state), "is_configured", property(lambda self: True))
    from features.workflows.notiz_workflow import NotizWorkflow
    monkeypatch.setattr(NotizWorkflow, "start", lambda self: started.append(self))
    from features.workflows.base_workflow import WorkflowType
    for wtype in WorkflowType:
        state.start_workflow(wtype)
    assert started == [] and state.active_workflow is None
    assert "richtet sich noch ein" in state.notification and "654 MB" in state.notification


def test_protokoll_import_ist_waehrend_der_einrichtung_gesperrt(world):
    state = _app()
    las._set(las.WORKING, "Lade Gemma 4 E4B …")
    state.import_file_for_protokoll("x.txt")
    assert state.active_workflow is None and "richtet sich noch ein" in state.notification


def test_nach_der_einrichtung_ist_die_app_frei(world):
    state = _app()
    las._set(las.READY, "Lokale KI bereit: Gemma 4 E4B")
    assert state.setup_busy() is None
    las._set(las.FAILED, "keine Internetverbindung")             # ein Fehler sperrt nicht für immer
    assert state.setup_busy() is None


def test_spracherkennungs_modell_wird_noch_geladen(world, monkeypatch):
    from services import local_transcription_service as lts
    state = _app()
    state.settings.transcription_backend = "local"
    monkeypatch.setattr(lts, "_PRELOADING", True)
    assert "Spracherkennungs-Modell" in state.setup_busy()
    state.settings.transcription_backend = "online"                # Online-Transkription braucht es nicht
    assert state.setup_busy() is None


def test_vorladen_merkt_sich_sofort_dass_es_laeuft(world, monkeypatch):
    from services import local_transcription_service as lts
    release = threading.Event()
    monkeypatch.setattr(lts, "AVAILABLE", True)
    monkeypatch.setattr(lts, "is_model_cached", lambda name: False)
    monkeypatch.setattr(lts, "_load_model", lambda name: release.wait(5))
    monkeypatch.setattr(lts, "_PRELOADING", False)
    lts.start_preload()
    assert lts.is_preloading()                                    # schon vor dem Thread-Start gesperrt
    release.set()
    import time
    for _ in range(50):
        if not lts.is_preloading():
            break
        time.sleep(0.05)
    assert not lts.is_preloading()


def test_gecachtes_modell_sperrt_nicht(world, monkeypatch):
    from services import local_transcription_service as lts
    monkeypatch.setattr(lts, "AVAILABLE", True)
    monkeypatch.setattr(lts, "is_model_cached", lambda name: True)
    monkeypatch.setattr(lts, "_PRELOADING", False)
    lts.start_preload()
    assert not lts.is_preloading()


def test_stuerzt_die_einrichtung_ab_bleibt_die_app_nicht_gesperrt(world, monkeypatch):
    state = _app()
    state.settings.llm_provider = "custom"
    monkeypatch.setattr(las, "run", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("kaputt")))
    state.start_local_ai_setup()
    import time
    for _ in range(100):
        if not las.is_working():
            break
        time.sleep(0.05)
    assert las.status.state == las.FAILED and "kaputt" in las.status.message
    assert state.setup_busy() is None


def test_start_sperrt_sofort_bevor_der_thread_laeuft(world, monkeypatch):
    state = _app()
    state.settings.llm_provider = "custom"
    release = threading.Event()
    monkeypatch.setattr(las, "run", lambda *a, **k: release.wait(5))
    state.start_local_ai_setup()
    assert state.setup_busy() is not None                         # schon beim Rückkehren gesperrt
    las._set(las.IDLE)
    release.set()
