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
