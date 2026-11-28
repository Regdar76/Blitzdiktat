# Copyright (c) 2026 Thorben Meier. MIT License.
"""Stufenweiser Selbststart von LM Studio und Laden des Modells (ohne echtes LM Studio)."""

import socket

import pytest

from services import local_server

URL = "http://localhost:1234/v1"
LMS = r"C:\lms.exe"
APP = r"C:\LM Studio.exe"


@pytest.fixture(autouse=True)
def isolated(monkeypatch):
    monkeypatch.setattr(local_server, "_last_failure", 0.0)
    monkeypatch.setattr(local_server, "_last_reason", "")
    local_server.forget_loaded()
    monkeypatch.setattr(local_server, "_launch_app", lambda app: pytest.fail("darf LM Studio nicht öffnen"))
    monkeypatch.setattr(local_server, "run_lms", lambda *a, **k: pytest.fail("darf lms nicht ausführen"))
    monkeypatch.setattr(local_server, "_AFTER_LAUNCH_FIRST", 0.0)
    monkeypatch.setattr(local_server, "_AFTER_LAUNCH_SECOND", 0.0)
    monkeypatch.setattr(local_server.time, "sleep", lambda s: None)


def _fake_clock(monkeypatch):
    ticks = iter(range(0, 100_000))
    monkeypatch.setattr(local_server.time, "monotonic", lambda: float(next(ticks)))


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


# ── Stufen beim Start ───────────────────────────────────────────────────────

def test_knopf_in_den_einstellungen_ignoriert_die_pause(monkeypatch):
    calls: list[int] = []
    monkeypatch.setattr(local_server, "find_lms", lambda: calls.append(1) or None)
    monkeypatch.setattr(local_server, "find_app", lambda: None)
    url = f"http://127.0.0.1:{_free_port()}/v1"
    assert not local_server.start_local_server(url)
    assert not local_server.start_local_server(url)             # Pause: kein neuer Versuch
    assert not local_server.start_local_server(url, force=True)
    assert len(calls) == 2


def test_lms_hilft_nicht_dann_wird_lm_studio_geoeffnet_und_erneut_gestartet(monkeypatch):
    events: list[str] = []
    up = {"v": False}
    monkeypatch.setattr(local_server, "find_lms", lambda: LMS)
    monkeypatch.setattr(local_server, "find_app", lambda: APP)

    def start(lms, port):
        events.append("start")
        up["v"] = "launch" in events                  # klappt erst, wenn LM Studio offen ist
        return up["v"]

    monkeypatch.setattr(local_server, "_start", start)
    monkeypatch.setattr(local_server, "_launch_app", lambda app: events.append("launch") or True)
    monkeypatch.setattr(local_server, "_wait_until_reachable", lambda url, wait: up["v"])
    monkeypatch.setattr(local_server, "is_reachable", lambda url, timeout=1.5: up["v"])
    assert local_server.start_local_server(URL, wait=20).ok
    assert events == ["start", "launch", "start"]


def test_ohne_lms_wird_lm_studio_geoeffnet_und_lms_danach_gefunden(monkeypatch):
    state = {"lms": None, "up": False}
    started: list[str] = []
    monkeypatch.setattr(local_server, "find_lms", lambda: state["lms"])   # erscheint erst nach dem Öffnen
    monkeypatch.setattr(local_server, "find_app", lambda: APP)
    monkeypatch.setattr(local_server, "_launch_app", lambda app: state.update(lms=LMS) or True)
    monkeypatch.setattr(local_server, "_start", lambda lms, p: started.append(lms) or state.update(up=True) or True)
    monkeypatch.setattr(local_server, "is_reachable", lambda url, timeout=1.5: state["up"])
    assert local_server.start_local_server(URL, wait=20).ok
    assert started == [LMS]


def test_lm_studio_offen_aber_kein_server_gibt_klare_meldung(monkeypatch):
    monkeypatch.setattr(local_server, "find_lms", lambda: LMS)
    monkeypatch.setattr(local_server, "find_app", lambda: APP)
    monkeypatch.setattr(local_server, "_start", lambda lms, p: False)
    monkeypatch.setattr(local_server, "_launch_app", lambda app: True)
    monkeypatch.setattr(local_server, "is_reachable", lambda url, timeout=1.5: False)
    _fake_clock(monkeypatch)
    result = local_server.start_local_server(URL, wait=30)
    assert not result.ok
    assert "Developer" in result.reason and "1234" in result.reason


def test_lm_studio_laesst_sich_nicht_oeffnen(monkeypatch):
    monkeypatch.setattr(local_server, "find_lms", lambda: None)
    monkeypatch.setattr(local_server, "find_app", lambda: APP)
    monkeypatch.setattr(local_server, "_launch_app", lambda app: False)
    monkeypatch.setattr(local_server, "is_reachable", lambda url, timeout=1.5: False)
    result = local_server.start_local_server(URL)
    assert not result.ok and "geöffnet" in result.reason


def test_lm_studio_wird_im_programmordner_gefunden(monkeypatch, tmp_path):
    exe = tmp_path / "local" / "Programs" / "LM Studio" / "LM Studio.exe"
    exe.parent.mkdir(parents=True)
    exe.write_bytes(b"")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    monkeypatch.setenv("ProgramFiles", str(tmp_path / "leer"))
    monkeypatch.setenv("ProgramFiles(x86)", str(tmp_path / "leer"))
    assert local_server.find_app() == str(exe)


# ── Modell laden ────────────────────────────────────────────────────────────

def test_geladenes_modell_wird_nicht_noch_einmal_geladen(monkeypatch):
    calls: list[tuple] = []
    monkeypatch.setattr(local_server, "find_lms", lambda: LMS)

    def fake(lms, *args, timeout=120):
        calls.append(args)
        return 0, '[{"identifier": "gemma-4-e2b-it", "modelKey": "gemma-4-e2b-it"}]'

    monkeypatch.setattr(local_server, "run_lms", fake)
    assert local_server.ensure_model_loaded(URL, "gemma-4-e2b-it")
    assert local_server.ensure_model_loaded(URL, "gemma-4-e2b-it")
    assert calls == [("ps", "--json")]                  # beim zweiten Mal gemerkt


def test_fehlendes_modell_wird_mit_kontextlaenge_geladen(monkeypatch):
    calls: list[tuple] = []
    monkeypatch.setattr(local_server, "find_lms", lambda: LMS)

    def fake(lms, *args, timeout=120):
        calls.append(args)
        return 0, "[]"

    monkeypatch.setattr(local_server, "run_lms", fake)
    assert local_server.ensure_model_loaded(URL, "qwen/qwen3.5-9b")
    assert calls[1] == ("load", "qwen/qwen3.5-9b", "-c", str(local_server.CONTEXT_LENGTH), "-y")


def test_modellname_wird_ohne_herausgeber_verglichen(monkeypatch):
    monkeypatch.setattr(local_server, "find_lms", lambda: LMS)
    monkeypatch.setattr(local_server, "run_lms", lambda lms, *a, timeout=120: (0, '[{"identifier": "qwen3.5-9b"}]'))
    assert local_server.ensure_model_loaded(URL, "qwen/qwen3.5-9b")


def test_laden_fehlgeschlagen_bleibt_beim_automatischen_laden(monkeypatch):
    monkeypatch.setattr(local_server, "find_lms", lambda: LMS)
    monkeypatch.setattr(
        local_server, "run_lms",
        lambda lms, *a, timeout=120: (0, "[]") if a[0] == "ps" else (1, "zu wenig Speicher"),
    )
    assert local_server.ensure_model_loaded(URL, "gemma") is False


def test_unlesbare_ps_ausgabe_fuehrt_zum_laden(monkeypatch):
    calls: list[tuple] = []
    monkeypatch.setattr(local_server, "find_lms", lambda: LMS)

    def fake(lms, *args, timeout=120):
        calls.append(args)
        return 0, "kein json"

    monkeypatch.setattr(local_server, "run_lms", fake)
    assert local_server.ensure_model_loaded(URL, "gemma")
    assert calls[1][0] == "load"


def test_fremder_server_wird_nie_mit_lms_beladen():
    assert local_server.ensure_model_loaded("https://ki.firma.example/v1", "gemma") is False
