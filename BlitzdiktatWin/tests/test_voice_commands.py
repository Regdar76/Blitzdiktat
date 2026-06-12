# Copyright (c) 2026 Thorben Meier. MIT License.
"""Tests für gesprochene Steuerkommandos (apply_voice_commands)."""

from services.transcription_service import apply_voice_commands


class TestAbsatz:
    def test_absatz_wird_zeilenumbruch(self):
        assert apply_voice_commands("Hallo Absatz wie geht es dir") == "Hallo\nwie geht es dir"

    def test_absatz_mit_satzzeichen(self):
        assert apply_voice_commands("Erster Satz. Absatz. Zweiter Satz.") == "Erster Satz\nZweiter Satz."

    def test_absatz_kleingeschrieben(self):
        assert apply_voice_commands("eins absatz zwei") == "eins\nzwei"

    def test_absatz_als_wortbestandteil_bleibt(self):
        # "Absatzformat" oder "Schuhabsatz" dürfen nicht ersetzt werden
        assert "Absatzformat" in apply_voice_commands("Das Absatzformat ist wichtig")
        assert "Schuhabsatz" in apply_voice_commands("Der Schuhabsatz ist kaputt")

    def test_text_ohne_kommando_bleibt_unveraendert(self):
        text = "Ein ganz normaler Satz ohne Kommandos."
        assert apply_voice_commands(text) == text


class TestAufzaehlung:
    def test_einfache_aufzaehlung(self):
        result = apply_voice_commands("Aufzählung Äpfel, Birnen, Kiwis Aufzählung Ende")
        assert "1. Äpfel" in result
        assert "2. Birnen" in result
        assert "3. Kiwis" in result

    def test_und_als_trennzeichen(self):
        result = apply_voice_commands("Aufzählung Brot und Butter Aufzählung Ende")
        assert "1. Brot" in result
        assert "2. Butter" in result

    def test_dezimalzahlen_werden_nicht_getrennt(self):
        result = apply_voice_commands("Aufzählung Version 1.5, Version 2.0 Aufzählung Ende")
        assert "Version 1.5" in result
        assert "Version 2.0" in result

    def test_text_um_aufzaehlung_bleibt(self):
        result = apply_voice_commands("Vorher Aufzählung eins, zwei Aufzählung Ende nachher")
        assert result.startswith("Vorher")
        assert result.rstrip().endswith("nachher")

    def test_whisper_schreibweise_aufzaehlung_komma_ende(self):
        # Whisper transkribiert oft "Aufzählung, Ende"
        result = apply_voice_commands("Aufzählung eins, zwei Aufzählung, Ende")
        assert "1. eins" in result
        assert "2. zwei" in result
