# Copyright (c) 2026 Thorben Meier. MIT License.
"""Tests für kleine Hilfsfunktionen (credentials, transcript_store, hotkeys)."""

from services.credentials_service import masked_display
from services.transcript_store import _md_inline, _xml_escape
from services.hotkey_service import HotkeyService


class TestMaskedDisplay:
    def test_langer_key_zeigt_nur_anfang(self):
        assert masked_display("sk-1234567890abcdef") == "sk-1 ••••••••"

    def test_kurzer_key_komplett_maskiert(self):
        assert masked_display("kurz") == "••••••••"

    def test_leerer_key(self):
        assert masked_display("") == ""


class TestPdfTextEscaping:
    def test_xml_escape(self):
        assert _xml_escape("a < b & c > d") == "a &lt; b &amp; c &gt; d"

    def test_bold_markdown(self):
        assert _md_inline("Das ist **wichtig** hier") == "Das ist <b>wichtig</b> hier"

    def test_bold_mit_sonderzeichen(self):
        # Escaping muss VOR der Bold-Umwandlung passieren
        assert _md_inline("**a & b**") == "<b>a &amp; b</b>"


class TestHotkeyParse:
    def test_combo_parsing(self):
        assert HotkeyService._parse("ctrl+shift+r") == frozenset({"ctrl", "shift", "r"})

    def test_case_insensitive(self):
        assert HotkeyService._parse("Ctrl+Shift+R") == HotkeyService._parse("ctrl+shift+r")
