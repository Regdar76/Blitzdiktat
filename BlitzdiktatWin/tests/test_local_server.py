# Copyright (c) 2026 Thorben Meier. MIT License.
"""Tests für den Selbststart des LM-Studio-Servers und die Übernahme der Installer-Vorgaben."""

import json
import socket

import pytest

import app_state
from services import local_server


@pytest.fixture(autouse=True)
def reset(monkeypatch):
    monkeypatch.setattr(local_server, "_last_failure", 0.0)
    monkeypatch.setattr(local_server, "_last_reason", "")
    local_server.forget_loaded()
    # Kein Test darf LM Studio auf diesem Rechner öffnen oder "lms" ausführen.
    monkeypatch.setattr(local_server, "_launch_app", lambda app: pytest.fail("darf LM Studio nicht öffnen"))
    monkeypatch.setattr(local_server, "run_lms", lambda *a, **k: pytest.fail("darf lms nicht ausführen"))


@pytest.mark.parametrize("url, expected", [
    ("http://localhost:1234/v1", ("localhost", 1234)),
    ("http://127.0.0.1:8080/v1", ("127.0.0.1", 8080)),
    ("https://ki.firma.example/api/v1", ("ki.firma.example", 443)),
    ("localhost:1234", ("localhost", 1234)),
])
def test_host_und_port(url, expected):
    assert local_server.host_and_port(url) == expected


def test_nur_dieser_rechner_gilt_als_lokal():
    assert local_server.is_local_url("http://localhost:1234/v1")
    assert local_server.is_local_url("http://127.0.0.1:1234/v1")
    assert not local_server.is_local_url("http://192.168.1.20:1234/v1")
    assert not local_server.is_local_url("https://ki.firma.example/v1")


def test_fremder_server_wird_nie_gestartet(monkeypatch):
    monkeypatch.setattr(local_server, "_start", lambda lms, port: pytest.fail("darf nicht starten"))
    assert local_server.ensure_running("https://ki.firma.example/v1") is False


def test_laufender_server_wird_nicht_noch_einmal_gestartet(monkeypatch):
    monkeypatch.setattr(local_server, "_start", lambda lms, port: pytest.fail("darf nicht starten"))
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        port = server.getsockname()[1]
        assert local_server.ensure_running(f"http://127.0.0.1:{port}/v1") is True


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_ohne_lm_studio_kein_start_und_keine_dauerschleife(monkeypatch):
    calls: list[int] = []
    monkeypatch.setattr(local_server, "find_lms", lambda: calls.append(1) or None)
    monkeypatch.setattr(local_server, "find_app", lambda: None)
    url = f"http://127.0.0.1:{_free_port()}/v1"
    assert local_server.ensure_running(url) is False
    assert local_server.ensure_running(url) is False      # Pause nach Fehlversuch
    assert len(calls) == 1
    assert "nicht installiert" in local_server.last_reason()


def test_start_mit_richtigem_port(monkeypatch):
    port = _free_port()
    started: list[tuple[str, int]] = []
    monkeypatch.setattr(local_server, "find_lms", lambda: r"C:\lms.exe")
    monkeypatch.setattr(local_server, "_start", lambda lms, p: started.append((lms, p)) or True)
    monkeypatch.setattr(local_server, "_wait_until_reachable", lambda url, wait: True)
    assert local_server.ensure_running(f"http://localhost:{port}/v1") is True
    assert started == [(r"C:\lms.exe", port)]


def test_lms_wird_im_profil_gefunden(monkeypatch, tmp_path):
    lms = tmp_path / ".lmstudio" / "bin" / "lms.exe"
    lms.parent.mkdir(parents=True)
    lms.write_bytes(b"")
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "leer"))
    assert local_server.find_lms() == str(lms)


def test_lms_wird_im_programmordner_gefunden(monkeypatch, tmp_path):
    lms = tmp_path / "local" / "Programs" / "LM Studio" / "resources" / "app" / ".webpack" / "lms.exe"
    lms.parent.mkdir(parents=True)
    lms.write_bytes(b"")
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    assert local_server.find_lms() == str(lms)


# ── Vorgaben des Installers ─────────────────────────────────────────────────

def test_installer_vorgabe_wird_einmalig_uebernommen(monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    folder = tmp_path / "Blitzdiktat"
    folder.mkdir()
    marker = folder / app_state.LOCAL_AI_SETUP_FILE
    marker.write_text(json.dumps({
        "provider": "custom", "base_url": "http://localhost:1234/v1", "model": "gemma-4-e2b-it",
    }), encoding="utf-8")

    s = app_state.AppSettings()
    assert app_state._apply_local_ai_setup(s) is True
    assert (s.llm_provider, s.custom_llm_model) == ("custom", "gemma-4-e2b-it")
    assert not marker.exists()                                   # nur einmal
    assert app_state._load_settings().llm_provider == "custom"   # gespeichert
    assert app_state._apply_local_ai_setup(app_state.AppSettings()) is False


def test_kaputte_installer_vorgabe_aendert_nichts(monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    folder = tmp_path / "Blitzdiktat"
    folder.mkdir()
    marker = folder / app_state.LOCAL_AI_SETUP_FILE
    marker.write_text("kein json", encoding="utf-8")
    s = app_state.AppSettings()
    assert app_state._apply_local_ai_setup(s) is False
    assert s.llm_provider == "openai"
    assert not marker.exists()
