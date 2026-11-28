# Copyright (c) 2026 Thorben Meier. MIT License.
"""Tests für die konfigurierbaren OpenAI-Modellnamen."""

import pytest

from services import llm_service, transcription_service


@pytest.fixture(autouse=True)
def reset_models():
    yield
    llm_service.set_models()
    transcription_service.set_transcription_model()


def test_defaults():
    llm_service.set_models()
    assert llm_service._model_fast == llm_service.DEFAULT_MODEL_FAST
    assert llm_service._model_quality == llm_service.DEFAULT_MODEL_QUALITY

def test_override():
    llm_service.set_models(fast="gpt-4.1-mini", quality="gpt-4.1")
    assert llm_service._model_fast == "gpt-4.1-mini"
    assert llm_service._model_quality == "gpt-4.1"

def test_leere_strings_ergeben_default():
    llm_service.set_models(fast="", quality="   ")
    assert llm_service._model_fast == llm_service.DEFAULT_MODEL_FAST
    assert llm_service._model_quality == llm_service.DEFAULT_MODEL_QUALITY

def test_transcription_model_override():
    transcription_service.set_transcription_model("gpt-4o-transcribe")
    assert transcription_service._transcription_model == "gpt-4o-transcribe"
    transcription_service.set_transcription_model("")
    assert transcription_service._transcription_model == transcription_service.DEFAULT_TRANSCRIPTION_MODEL


# ── Umbenanntes Modell im eigenen Server ────────────────────────────────────

def test_veralteter_modellname_wird_automatisch_angepasst(monkeypatch):
    import app_state
    state = app_state.AppState.__new__(app_state.AppState)
    state.settings = app_state.AppSettings()
    state.settings.llm_provider = "custom"
    state.settings.custom_llm_model = "gemma-4-e2b-it"
    saved: list[str] = []
    monkeypatch.setattr(app_state.AppState, "save_ai_settings", lambda self: saved.append(self.settings.custom_llm_model))
    assert state.heal_local_model(["google/gemma-4-e2b", "text-embedding-x"]) is True
    assert state.settings.custom_llm_model == "google/gemma-4-e2b" and saved == ["google/gemma-4-e2b"]
    assert state.heal_local_model(["google/gemma-4-e2b"]) is False        # nichts mehr zu tun


def test_openai_einstellung_bleibt_beim_heilen_unberuehrt(monkeypatch):
    import app_state
    state = app_state.AppState.__new__(app_state.AppState)
    state.settings = app_state.AppSettings()
    state.settings.custom_llm_model = "gemma-4-e2b-it"            # Anbieter bleibt "openai"
    assert state.heal_local_model(["google/gemma-4-e2b"]) is False
    assert state.settings.custom_llm_model == "gemma-4-e2b-it"
