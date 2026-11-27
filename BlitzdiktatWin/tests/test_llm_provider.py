# Copyright (c) 2026 Thorben Meier. MIT License.
"""Tests für die Anbieterwahl der Text-KI (OpenAI oder eigener Server)."""

import asyncio
import datetime as dt
from types import SimpleNamespace

import pytest
from openai import APIConnectionError, APITimeoutError, BadRequestError

from services import llm_service, prompts


@pytest.fixture(autouse=True)
def reset_provider(monkeypatch):
    # Kein Test darf den echten Windows-Schlüsselspeicher lesen.
    monkeypatch.setattr(llm_service, "load_api_key", lambda: None)
    monkeypatch.setattr(llm_service.credentials_service, "load_custom_api_key", lambda: None)
    # ... und keiner darf LM Studio auf dem Rechner starten.
    monkeypatch.setattr(llm_service.local_server, "ensure_running", lambda url: False)
    # Andere Tests erzeugen einen AppState, der die echten Einstellungen des
    # Rechners übernimmt – deshalb auch vorher auf den Standard zurücksetzen.
    llm_service.configure_provider()
    llm_service.set_models()
    yield
    llm_service.configure_provider()
    llm_service.set_models()


def run(coro):
    return asyncio.run(coro)


@pytest.fixture
def captured(monkeypatch):
    """Ersetzt den Netzaufruf und merkt sich, was gesendet worden wäre."""
    calls: list[dict] = []

    async def fake_complete(text, system_prompt, model, temperature):
        calls.append(dict(text=text, system=system_prompt, model=model, temperature=temperature))
        return "## Protokoll\n* Punkt"

    monkeypatch.setattr(llm_service, "_complete", fake_complete)
    return calls


# ── Konfiguration ───────────────────────────────────────────────────────────

def test_standard_ist_openai():
    llm_service.configure_provider()
    assert not llm_service.is_custom()


def test_unbekannter_anbieter_faellt_auf_openai_zurueck():
    llm_service.configure_provider("irgendwas", "http://x/v1", "m")
    assert not llm_service.is_custom()


@pytest.mark.parametrize("raw, expected", [
    ("localhost:1234", "http://localhost:1234/v1"),
    ("http://localhost:1234", "http://localhost:1234/v1"),
    ("http://localhost:1234/v1/", "http://localhost:1234/v1"),
    ("https://ki.firma.example/api/v1", "https://ki.firma.example/api/v1"),
    ("  ", ""),
])
def test_adresse_wird_ergaenzt(raw, expected):
    assert llm_service.normalize_base_url(raw) == expected


def test_config_problem_openai_ohne_key():
    llm_service.configure_provider("openai")
    assert "API Key" in llm_service.config_problem()
    assert not llm_service.is_available()


def test_config_problem_openai_mit_key(monkeypatch):
    monkeypatch.setattr(llm_service, "load_api_key", lambda: "sk-test")
    assert llm_service.config_problem() is None


def test_eigener_server_braucht_modell_aber_keinen_key():
    llm_service.configure_provider("custom", "localhost:1234", "")
    assert "Modell" in llm_service.config_problem()
    llm_service.configure_provider("custom", "localhost:1234", "gemma-4-e2b-it")
    assert llm_service.config_problem() is None
    assert llm_service.is_available()


# ── Prompt-Auswahl ──────────────────────────────────────────────────────────

def test_dampf_openai_nutzt_standardprompt(captured):
    run(llm_service.dampf_ablassen("so ein Mist"))
    assert captured[0]["system"] == prompts.DAMPF_SYSTEM_PROMPT
    assert captured[0]["text"] == "so ein Mist"


def test_dampf_eigener_server_nutzt_lokalen_prompt(captured):
    llm_service.configure_provider("custom", "", "gemma")
    run(llm_service.dampf_ablassen("so ein Mist"))
    assert captured[0]["system"] == prompts.DAMPF_LOCAL_SYSTEM_PROMPT
    assert '"""\nso ein Mist\n"""' in captured[0]["text"]
    assert captured[0]["temperature"] == 0.2


def test_eigener_prompt_des_nutzers_hat_vorrang(captured):
    llm_service.configure_provider("custom", "", "gemma")
    run(llm_service.dampf_ablassen("so ein Mist", "Mein Prompt"))
    run(llm_service.protokoll("Wir treffen uns.", "Mein Protokoll-Prompt", dt.date(2026, 11, 26)))
    assert captured[0]["system"] == "Mein Prompt" and captured[0]["text"] == "so ein Mist"
    assert captured[1]["system"] == "Mein Protokoll-Prompt"


def test_protokoll_rechnet_daten_vorab_aus(captured):
    run(llm_service.protokoll("Das schicke ich bis nächsten Dienstag.", today=dt.date(2026, 11, 26)))
    sent = captured[0]["text"]
    assert sent.startswith("Aufnahmedatum: Donnerstag, 26.11.2026")
    assert "bis nächsten Dienstag (01.12.2026)" in sent
    assert prompts.DATE_HINT in sent
    assert captured[0]["system"] == prompts.PROTOKOLL_SYSTEM_PROMPT


def test_protokoll_ohne_zeitangaben_bleibt_ohne_hinweis(captured):
    run(llm_service.protokoll("Der Estrich ist trocken.", today=dt.date(2026, 11, 26)))
    assert captured[0]["text"] == "Aufnahmedatum: Donnerstag, 26.11.2026\n\nDer Estrich ist trocken."


def test_protokoll_ausgabe_wird_gesaeubert(captured):
    out = run(llm_service.protokoll("x", today=dt.date(2026, 11, 26)))
    assert out == "## Protokoll\n- Punkt"


def test_protokoll_eigener_server(captured):
    llm_service.configure_provider("custom", "", "gemma")
    out = run(llm_service.protokoll("Abgabe bis Freitag.", today=dt.date(2026, 11, 26)))
    assert captured[0]["system"] == prompts.PROTOKOLL_LOCAL_SYSTEM_PROMPT
    assert "bis Freitag (27.11.2026)" in captured[0]["text"]
    assert captured[0]["temperature"] == 0.1
    assert out.endswith(prompts.LOCAL_PROTOCOL_NOTE)


# ── Aufruf des eigenen Servers ──────────────────────────────────────────────

class FakeClient:
    """Stellt AsyncOpenAI nach und merkt sich Konstruktor- und Aufrufparameter."""
    instances: list["FakeClient"] = []
    failures: list[Exception] = []
    answer = "Guten Tag,"

    def __init__(self, **kwargs):
        self.init = kwargs
        self.calls: list[dict] = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))
        FakeClient.instances.append(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        self.closed = True

    async def _create(self, **kwargs):
        self.calls.append(kwargs)
        if FakeClient.failures:
            raise FakeClient.failures.pop(0)
        msg = SimpleNamespace(content=FakeClient.answer)
        return SimpleNamespace(choices=[SimpleNamespace(message=msg)])


@pytest.fixture
def fake_client(monkeypatch):
    FakeClient.instances, FakeClient.failures, FakeClient.answer = [], [], "Guten Tag,"
    monkeypatch.setattr(llm_service, "AsyncOpenAI", FakeClient)
    return FakeClient


# Anfrage und Antwort nur nachgestellt: Je nach Version bringt das openai-Paket
# "httpx" oder "httpx2" mit – die Tests sollen von beidem unabhängig sein.
def _request():
    return SimpleNamespace(method="POST", url="http://localhost:1234/v1/chat/completions")


def _response(status_code: int):
    return SimpleNamespace(status_code=status_code, request=_request(), headers={})


def test_eigener_server_bekommt_adresse_modell_und_denkmodus_aus(fake_client):
    llm_service.configure_provider("custom", "localhost:1234", "gemma-4-e2b-it")
    assert run(llm_service._complete("hallo", "sys", "gpt-4o", 0.3)) == "Guten Tag,"
    client = fake_client.instances[0]
    assert client.init["base_url"] == "http://localhost:1234/v1"
    assert client.calls[0]["model"] == "gemma-4-e2b-it"          # nicht das OpenAI-Modell
    assert client.calls[0]["extra_body"] == {"reasoning_effort": "none"}
    assert client.closed                                         # Verbindung geschlossen


def test_denkmodus_parameter_abschaltbar(fake_client):
    llm_service.configure_provider("custom", "", "gemma", disable_thinking=False)
    run(llm_service._complete("hallo", "sys", "x", 0.3))
    assert fake_client.instances[0].calls[0]["extra_body"] is None


def test_server_ohne_denkmodus_parameter_wird_erneut_gefragt(fake_client):
    llm_service.configure_provider("custom", "", "gemma")
    fake_client.failures = [BadRequestError("unknown field", response=_response(400), body=None)]
    assert run(llm_service._complete("hallo", "sys", "x", 0.3)) == "Guten Tag,"
    calls = fake_client.instances[0].calls
    assert len(calls) == 2 and "extra_body" not in calls[1]


def test_nicht_erreichbarer_server_gibt_klare_meldung(fake_client):
    llm_service.configure_provider("custom", "localhost:1234", "gemma")
    fake_client.failures = [APIConnectionError(request=_request())]
    with pytest.raises(llm_service.LLMError, match="nicht erreichbar"):
        run(llm_service._complete("hallo", "sys", "x", 0.3))


def test_nicht_erreichbarer_fremder_server_nennt_die_adresse(fake_client):
    llm_service.configure_provider("custom", "https://ki.firma.example/v1", "gemma")
    fake_client.failures = [APIConnectionError(request=_request())]
    with pytest.raises(llm_service.LLMError, match=r"ki\.firma\.example.*Läuft er"):
        run(llm_service._complete("hallo", "sys", "x", 0.3))


def test_lokaler_server_wird_gestartet_und_die_anfrage_wiederholt(fake_client, monkeypatch):
    started: list[str] = []
    monkeypatch.setattr(
        llm_service.local_server, "ensure_running", lambda url: started.append(url) or True,
    )
    llm_service.configure_provider("custom", "localhost:1234", "gemma")
    fake_client.failures = [APIConnectionError(request=_request())]
    assert run(llm_service._complete("hallo", "sys", "x", 0.3)) == "Guten Tag,"
    assert started == ["http://localhost:1234/v1"]
    assert len(fake_client.instances) == 2          # zweiter Versuch nach dem Start


def test_zeitueberschreitung_startet_keinen_server(fake_client, monkeypatch):
    started: list[str] = []
    monkeypatch.setattr(
        llm_service.local_server, "ensure_running", lambda url: started.append(url) or True,
    )
    llm_service.configure_provider("custom", "localhost:1234", "gemma")
    fake_client.failures = [APITimeoutError(request=_request())]
    with pytest.raises(llm_service.LLMError, match="nicht rechtzeitig"):
        run(llm_service._complete("hallo", "sys", "x", 0.3))
    assert not started


def test_anrede_bleibt_im_verbesserungs_prompt_erhalten():
    settings = SimpleNamespace(system_prompt="", tone="neutral", context="", custom_terms=[])
    assert "Anrede" in llm_service._build_improvement_prompt(settings)


def test_eigener_server_ohne_modell(fake_client):
    llm_service.configure_provider("custom", "localhost:1234", "")
    with pytest.raises(llm_service.LLMError, match="kein Modell"):
        run(llm_service._complete("hallo", "sys", "x", 0.3))
    assert not fake_client.instances                # gar nicht erst verbunden


def test_denkblock_in_der_antwort_wird_entfernt(fake_client):
    llm_service.configure_provider("custom", "", "gemma")
    fake_client.answer = "<think>hm</think>\nGuten Tag,"
    assert run(llm_service._complete("hallo", "sys", "x", 0.3)) == "Guten Tag,"


def test_leere_antwort_ist_ein_fehler(fake_client):
    llm_service.configure_provider("custom", "", "gemma")
    fake_client.answer = "   "
    with pytest.raises(llm_service.LLMError, match="Keine Antwort"):
        run(llm_service._complete("hallo", "sys", "x", 0.3))


def test_openai_ohne_key_meldet_fehlenden_key(fake_client):
    llm_service.configure_provider("openai")
    with pytest.raises(llm_service.LLMError, match="API Key fehlt"):
        run(llm_service._complete("hallo", "sys", "gpt-4o", 0.3))


def test_openai_nutzt_uebergebenes_modell(fake_client, monkeypatch):
    monkeypatch.setattr(llm_service, "load_api_key", lambda: "sk-test")
    llm_service.configure_provider("openai")
    run(llm_service._complete("hallo", "sys", "gpt-4o", 0.3))
    client = fake_client.instances[0]
    assert "base_url" not in client.init
    assert client.calls[0]["model"] == "gpt-4o" and "extra_body" not in client.calls[0]
