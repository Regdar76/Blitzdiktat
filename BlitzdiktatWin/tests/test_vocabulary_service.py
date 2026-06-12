# Copyright (c) 2026 Thorben Meier. MIT License.
"""Tests für das gelernte Vokabular (vocabulary_service)."""

import pytest

from services import vocabulary_service


@pytest.fixture(autouse=True)
def isolated_appdata(tmp_path, monkeypatch):
    """Leitet %APPDATA% in ein Temp-Verzeichnis um, damit Tests keine echten Daten anfassen."""
    monkeypatch.setenv("APPDATA", str(tmp_path))


def test_leeres_vokabular_initial():
    assert vocabulary_service.get_learned_terms() == []

def test_terms_hinzufuegen_und_lesen():
    vocabulary_service.add_terms(["OpenAI", "München"])
    assert vocabulary_service.get_learned_terms() == ["OpenAI", "München"]

def test_duplikate_case_insensitive():
    vocabulary_service.add_terms(["OpenAI"])
    vocabulary_service.add_terms(["openai", "OPENAI", "Berlin"])
    assert vocabulary_service.get_learned_terms() == ["OpenAI", "Berlin"]

def test_leere_strings_werden_ignoriert():
    vocabulary_service.add_terms(["", "   ", "Echt"])
    assert vocabulary_service.get_learned_terms() == ["Echt"]

def test_max_terms_begrenzung():
    vocabulary_service.add_terms([f"Begriff{i}" for i in range(vocabulary_service.MAX_TERMS + 50)])
    terms = vocabulary_service.get_learned_terms()
    assert len(terms) == vocabulary_service.MAX_TERMS
    # Die ältesten fliegen raus, die neuesten bleiben
    assert terms[-1] == f"Begriff{vocabulary_service.MAX_TERMS + 49}"

def test_clear():
    vocabulary_service.add_terms(["Etwas"])
    vocabulary_service.clear()
    assert vocabulary_service.get_learned_terms() == []
