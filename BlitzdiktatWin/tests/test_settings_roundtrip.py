# Copyright (c) 2026 Thorben Meier. MIT License.
"""Tests für das Laden/Speichern der Settings (app_state)."""

import pytest

from app_state import AppSettings, _load_settings, _save_settings


@pytest.fixture(autouse=True)
def isolated_appdata(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))


def test_defaults_ohne_datei():
    s = _load_settings()
    assert s == AppSettings()

def test_roundtrip_erhaelt_alle_werte():
    s = AppSettings()
    s.language = "en"
    s.hotkey_transcription = "ctrl+alt+x"
    s.transcription_backend = "online"
    s.local_whisper_model = "medium"
    s.openai_model_fast = "gpt-4.1-mini"
    s.openai_model_quality = "gpt-4.1"
    s.openai_transcription_model = "whisper-1"
    s.text_improvement.tone = "formal"
    s.text_improvement.custom_terms = ["Karstens", "Blitzdiktat"]
    s.emoji_text.emoji_density = "viel"
    s.protokoll.custom_name = "Meeting-Notizen"

    _save_settings(s)
    loaded = _load_settings()
    assert loaded == s

def test_kaputte_datei_faellt_auf_defaults_zurueck(tmp_path):
    import os
    folder = os.path.join(str(tmp_path), "Blitzdiktat")
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "settings.json"), "w", encoding="utf-8") as f:
        f.write("{ kein gültiges json")
    assert _load_settings() == AppSettings()

def test_unbekannte_felder_werden_ignoriert(tmp_path):
    import json
    import os
    folder = os.path.join(str(tmp_path), "Blitzdiktat")
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "settings.json"), "w", encoding="utf-8") as f:
        json.dump({"language": "en", "zukunfts_feature": True}, f)
    s = _load_settings()
    assert s.language == "en"
