# Copyright (c) 2026 Thorben Meier. MIT License.
"""
In-App-Benutzerhandbuch für Blitzdiktat.
Zeigt alle Funktionen, Einstellungen und häufige Fragen als scrollbare Ansicht.
"""

import customtkinter as ctk
from services import paste_service


class HelpWindow(ctk.CTkToplevel):
    def __init__(self, parent, settings=None):
        super().__init__(parent)
        self._settings = settings
        self.title("Blitzdiktat – Benutzerhandbuch")
        self.geometry("640x720")
        self.resizable(True, True)
        self.attributes("-topmost", True)
        self.focus_force()
        paste_service.register_own_window(self.winfo_id())
        self._build()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self) -> None:
        scroll = ctk.CTkScrollableFrame(self)
        scroll.pack(fill="both", expand=True, padx=16, pady=16)

        s = self._settings
        hk_t  = getattr(s, "hotkey_transcription",  "ctrl+shift+r") if s else "ctrl+shift+r"
        hk_ti = getattr(s, "hotkey_text_improver",   "ctrl+shift+t") if s else "ctrl+shift+t"
        hk_d  = getattr(s, "hotkey_dampf_ablassen",  "ctrl+shift+d") if s else "ctrl+shift+d"
        hk_e  = getattr(s, "hotkey_emoji_text",      "ctrl+shift+e") if s else "ctrl+shift+e"
        hk_p  = getattr(s, "hotkey_protokoll",       "ctrl+shift+p") if s else "ctrl+shift+p"

        # ── Titel ──────────────────────────────────────────────────────
        ctk.CTkLabel(
            scroll,
            text="📖  Blitzdiktat – Benutzerhandbuch",
            font=ctk.CTkFont(size=18, weight="bold"),
            anchor="w",
        ).pack(fill="x", pady=(0, 2))
        ctk.CTkLabel(
            scroll,
            text="Sprach-zu-Text für Windows — schnell, lokal und KI-gestützt.",
            font=ctk.CTkFont(size=11),
            text_color=("#6B7280", "#9CA3AF"),
            anchor="w",
        ).pack(fill="x", pady=(0, 12))

        # ── Schnellstart ───────────────────────────────────────────────
        self._h2(scroll, "🚀  Schnellstart")
        self._text(scroll,
            "1.  API Key hinterlegen (Einstellungen → OpenAI API Key) "
            "— oder lokale Transkription aktivieren (kein API Key nötig).")
        self._text(scroll,
            "2.  Mikrofon auswählen oder das Standard-Mikrofon des Systems nutzen.")
        self._text(scroll,
            "3.  Tastenkürzel gedrückt halten → sprechen → loslassen "
            "→ Text erscheint automatisch in der aktiven Anwendung.")
        self._tip(scroll,
            "Blitzdiktat fügt den Text in das Fenster ein, das beim Drücken "
            "des Tastenkürzels aktiv war — also vorher ins Zielfenster klicken.")

        # ── Funktionen ─────────────────────────────────────────────────
        self._h2(scroll, "⚡  Die Funktionen im Überblick")

        # Blitzdiktat
        self._h3(scroll, "🎤  Blitzdiktat  —  Einfache Transkription")
        self._hotkey_row(scroll, hk_t, "Aufnahme → Transkribieren → Einfügen")
        self._text(scroll,
            "Die Grundfunktion: Nimmt das Gesprochene auf, wandelt es mit Whisper in Text um "
            "und fügt ihn direkt ins aktive Textfeld ein. Keine KI-Nachbearbeitung — "
            "reine Spracherkennung.")
        self._bullet(scroll, 'Sprachbefehl "Absatz" → fügt einen Zeilenumbruch ein')
        self._bullet(scroll, 'Sprachbefehl "Aufzählung … Aufzählung Ende" → erstellt eine nummerierte Liste')
        self._bullet(scroll,
            "Eigennamen und Fachbegriffe können in den Einstellungen hinterlegt werden, "
            "damit Whisper sie besser erkennt.")

        # Blitzdiktat+
        self._h3(scroll, "✨  Blitzdiktat+  —  Mit KI-Verbesserung")
        self._hotkey_row(scroll, hk_ti, "Transkription + automatische Textverbesserung durch GPT")
        self._text(scroll,
            "Wie Blitzdiktat, aber der transkribierte Text wird anschließend von GPT "
            "korrigiert und stilistisch verbessert — inklusive Grammatik und Formulierung.")
        self._bullet(scroll, "Ton wählbar: formal, neutral oder locker")
        self._bullet(scroll, 'Kontext optional angeben (z. B. "E-Mail an Kunden")')
        self._bullet(scroll, "Eigene Fachbegriffe werden korrekt übernommen")
        self._bullet(scroll, "Eigener System-Prompt möglich für vollständig individuelle Ausgabe")

        # Dampf ablassen
        self._h3(scroll, "💢  Blitzdiktat $%&!  —  Dampf ablassen")
        self._hotkey_row(scroll, hk_d, "Transkription + pointierte Umformulierung durch GPT")
        self._text(scroll,
            "Für frustrierte Momente: Der gesprochene Text wird von GPT scharf, direkt "
            "und ohne Beschönigung umformuliert. Eigener System-Prompt konfigurierbar.")

        # Emoji
        self._h3(scroll, "😊  Blitzdiktat :)  —  Mit Emojis")
        self._hotkey_row(scroll, hk_e, "Transkription + automatische Emoji-Ergänzung")
        self._text(scroll,
            "GPT ergänzt den transkribierten Text mit passenden Emojis. "
            "Die Dichte ist in den Einstellungen regelbar.")
        self._bullet(scroll, "Wenig: 1–2 Emojis pro Absatz")
        self._bullet(scroll, "Mittel: etwa alle 1–2 Sätze")
        self._bullet(scroll, "Viel: mehrere Emojis pro Satz")

        # Protokoll
        self._h3(scroll, "📋  Blitzdiktat Protokoll  —  Meeting-Protokoll")
        self._hotkey_row(scroll, hk_p, "Aufnahme → Transkription → strukturiertes Protokoll")
        self._text(scroll,
            "Nimmt eine Besprechung auf — oder importiert eine externe Audio- bzw. Textdatei — "
            "und erstellt daraus ein strukturiertes Markdown-Protokoll: einleitende Zusammenfassung "
            "(auch für Außenstehende verständlich), besprochene Punkte, Entscheidungen, offene Aufgaben "
            "und — falls genannt — der nächste Termin. Wird zusätzlich als PDF gespeichert.")
        self._bullet(scroll, "Aufnahme: Hotkey gedrückt halten → sprechen → loslassen")
        self._bullet(scroll, "Import: 📂-Button neben dem Protokoll-Button im Hauptfenster")
        self._bullet(
            scroll,
            "Unterstützte Audio-Formate: .wav  .mp3  .m4a  .ogg  .flac  .aac  .wma",
        )
        self._bullet(scroll, "Unterstützte Text-Formate: .txt  .md")
        self._bullet(
            scroll,
            "PDF wird automatisch unter "
            "%LOCALAPPDATA%\\Blitzdiktat\\Transkriptionen gespeichert.",
        )
        self._tip(scroll,
            "Den System-Prompt für Protokolle kann in den Einstellungen angepasst werden, "
            "um das Ausgabeformat an eigene Anforderungen anzupassen — z. B. für "
            "Bau- oder Projektbesprechungen.")

        # ── Einstellungen ──────────────────────────────────────────────
        self._h2(scroll, "⚙️  Einstellungen im Detail")

        self._h3(scroll, "Mikrofon")
        self._text(scroll,
            "Auswahl des Eingabegeräts für alle Aufnahmen. Der ↺-Button aktualisiert "
            "die Geräteliste, falls ein Mikrofon erst nach dem App-Start angeschlossen wurde.")

        self._h3(scroll, "Transkriptions-Backend")
        self._bullet(scroll,
            "☁️  Online (OpenAI Whisper API): Cloud-basiert, sehr präzise, "
            "benötigt API Key und Internetverbindung. Empfohlen für beste Qualität.")
        self._bullet(scroll,
            "🔒  Lokal (faster-whisper): Vollständig offline, kein API Key nötig. "
            "Das Modell wird beim ersten Einsatz einmalig automatisch heruntergeladen.")
        self._tip(scroll,
            "Bei Verbindungsproblemen wechselt die App automatisch auf lokale Transkription, "
            "falls faster-whisper installiert ist — ohne Fehlermeldung.")

        self._h3(scroll, "Whisper-Modell (nur für lokale Transkription)")
        self._bullet(scroll, "Tiny     (~75 MB)   — sehr schnell, weniger präzise")
        self._bullet(scroll, "Base     (~150 MB)  — schnell")
        self._bullet(scroll, "Small    (~500 MB)  — gute Balance  ✓  Empfohlen")
        self._bullet(scroll, "Medium   (~1,5 GB)  — präzise")
        self._bullet(scroll, "Large-v3 (~3 GB)    — beste Qualität")
        self._text(scroll,
            "Bereits heruntergeladene Modelle werden im Einstellungsdialog "
            "mit ✅ markiert.")

        self._h3(scroll, "OpenAI API Key")
        self._text(scroll,
            "Benötigt für alle Online-Funktionen: Online-Transkription, Blitzdiktat+, "
            "Protokoll, Dampf ablassen, Emoji. Der Key wird sicher im "
            "Windows-Schlüsselspeicher (Keyring) gespeichert — nicht im Klartext.")

        self._h3(scroll, "Sprache")
        self._text(scroll,
            "Sprache der Aufnahme. Whisper erkennt zuverlässig: "
            "de (Deutsch), en (Englisch), fr (Französisch), es (Spanisch), "
            "it (Italienisch), nl (Niederländisch), pl (Polnisch).")

        self._h3(scroll, "Darstellung")
        self._text(scroll,
            "Wählt zwischen System (folgt der Windows-Einstellung), Hell und Dunkel. "
            "Die Änderung ist sofort wirksam — kein Neustart nötig.")

        self._h3(scroll, "Eigennamen / Fachbegriffe (manuell)")
        self._text(scroll,
            "Komma-getrennte Liste von Begriffen, die Whisper besonders berücksichtigen soll — "
            "z. B. Projektnamen, seltene Eigennamen, Produktbezeichnungen. "
            "Verbessert die Erkennungsrate dieser Begriffe erheblich.")

        self._h3(scroll, "Gelerntes Vokabular (automatisch)")
        self._text(scroll,
            "Nach jeder Transkription extrahiert GPT automatisch Eigennamen und Fachbegriffe "
            "aus dem Text und speichert sie lokal. Bei zukünftigen Aufnahmen werden diese Begriffe "
            "automatisch an Whisper übergeben — die App lernt selbstständig mit der Zeit.")
        self._bullet(scroll,
            "Gespeichert in %APPDATA%\\Blitzdiktat\\vocabulary.json")
        self._bullet(scroll, "Maximal 150 Begriffe (älteste fallen heraus)")
        self._bullet(scroll,
            "Über \"Vokabular löschen\" in den Einstellungen kann die Liste zurückgesetzt werden")
        self._bullet(scroll,
            "Funktioniert nur, wenn ein OpenAI API Key hinterlegt ist")

        self._h3(scroll, "Tastenkürzel")
        self._text(scroll,
            "Jede Funktion besitzt ein frei konfigurierbares Tastenkürzel. "
            "Format: ctrl+shift+r, alt+r, ctrl+alt+t usw. "
            "Nach dem Speichern startet die App automatisch neu, "
            "damit die neuen Kürzel übernommen werden.")

        self._h3(scroll, "Blitzdiktat+ Einstellungen")
        self._bullet(scroll,
            "Ton: formal (Geschäftsstil), neutral (Standard), casual (locker/umgangssprachlich)")
        self._bullet(scroll,
            'Kontext: optionaler Hinweis für GPT, z. B. "E-Mail an Kunden" oder "Kurze Notiz"')
        self._bullet(scroll,
            "System-Prompt: eigener Prompt ersetzt den eingebauten vollständig")

        # ── System-Tray ────────────────────────────────────────────────
        self._h2(scroll, "🖥️  System-Tray & Hintergrundbetrieb")
        self._text(scroll,
            "Blitzdiktat läuft im Hintergrund und reagiert jederzeit auf Tastenkürzel — "
            "auch wenn das Hauptfenster geschlossen ist. Das App-Symbol erscheint "
            "in der Windows-Taskleiste (Infobereich/Tray).")
        self._bullet(scroll,
            "Rechtsklick auf das Tray-Symbol → \"Blitzdiktat anzeigen\" öffnet das Hauptfenster")
        self._bullet(scroll,
            "Rechtsklick → \"Beenden\" schließt die App vollständig")
        self._tip(scroll,
            "Das ✕ im Hauptfenster schließt nur das Fenster — die App läuft weiter. "
            "Zum vollständigen Beenden Rechtsklick → Beenden im Tray verwenden.")

        # ── FAQ ────────────────────────────────────────────────────────
        self._h2(scroll, "❓  Häufige Fragen")

        self._faq(scroll,
            "Die App erkennt meinen API Key nicht.",
            "Einstellungen öffnen → API Key in das Feld eingeben → \"API Key speichern\" klicken. "
            "Der Key wird sicher im Windows-Schlüsselspeicher gespeichert.")

        self._faq(scroll,
            "Es passiert nichts beim Drücken des Tastenkürzels.",
            "Sicherstellen, dass das richtige Mikrofon gewählt ist. Bei Online-Backend prüfen, "
            "ob eine Internetverbindung besteht und der API Key hinterlegt wurde. "
            "Im Hauptfenster erscheint eine Fehlermeldung bei Problemen.")

        self._faq(scroll,
            "Das lokale Whisper-Modell wird nicht geladen.",
            "Beim ersten Start wird das Small-Modell (~500 MB) automatisch heruntergeladen. "
            "Falls das fehlschlägt: im Terminal \"pip install faster-whisper\" ausführen "
            "und die App neu starten.")

        self._faq(scroll,
            "Text wird nicht eingefügt oder landet im falschen Fenster.",
            "Das Tastenkürzel muss gedrückt werden, solange das Zielfenster aktiv ist. "
            "Blitzdiktat merkt sich genau das Fenster, das beim Drücken des Kürzels im "
            "Vordergrund war.")

        self._faq(scroll,
            "Das Protokoll enthält keine Aufgaben oder Entscheidungen.",
            "Das Protokoll-Modell trägt nur ein, was im Gespräch klar genannt wurde. "
            "Falls das Format oder die Struktur angepasst werden soll, kann ein eigener "
            "System-Prompt in Einstellungen → Blitzdiktat Protokoll Einstellungen hinterlegt werden.")

        self._faq(scroll,
            "Transkription enthält häufig falsch geschriebene Namen.",
            "Eigennamen in Einstellungen → Eigennamen / Fachbegriffe eintragen. "
            "Nach einigen Transkriptionen lernt die App die Namen auch automatisch "
            "(Gelerntes Vokabular — erfordert API Key).")

        self._faq(scroll,
            "Kann ich Blitzdiktat in einer anderen Sprache nutzen?",
            "Ja. In den Einstellungen unter \"Sprache\" die gewünschte Sprache auswählen. "
            "Whisper erkennt dann Aufnahmen in dieser Sprache.")

        self._faq(scroll,
            "Wo werden Transkriptionen und Protokolle gespeichert?",
            "Alle Transkriptionen als .txt-Dateien und Protokolle als .pdf-Dateien "
            "werden in %LOCALAPPDATA%\\Blitzdiktat\\Transkriptionen gespeichert. "
            "Dateien älter als 14 Tage werden automatisch gelöscht.")

        ctk.CTkLabel(scroll, text="").pack(pady=8)

    # ------------------------------------------------------------------
    # Layout-Helfer
    # ------------------------------------------------------------------

    def _h2(self, parent, text: str) -> None:
        ctk.CTkLabel(
            parent, text=text,
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        ).pack(fill="x", pady=(16, 2))
        ctk.CTkFrame(parent, height=1, fg_color=("#D1D5DB", "#374151")).pack(
            fill="x", pady=(0, 6)
        )

    def _h3(self, parent, text: str) -> None:
        ctk.CTkLabel(
            parent, text=text,
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w",
        ).pack(fill="x", pady=(10, 2))

    def _text(self, parent, text: str) -> None:
        ctk.CTkLabel(
            parent, text=text,
            font=ctk.CTkFont(size=11),
            anchor="w", justify="left",
            wraplength=570,
        ).pack(fill="x", anchor="w", pady=(0, 4))

    def _bullet(self, parent, text: str) -> None:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=1)
        ctk.CTkLabel(
            row, text="·", width=20, anchor="center",
            font=ctk.CTkFont(size=14),
            text_color=("#6B7280", "#9CA3AF"),
        ).pack(side="left")
        ctk.CTkLabel(
            row, text=text,
            font=ctk.CTkFont(size=11),
            anchor="w", justify="left",
            wraplength=530,
        ).pack(side="left", fill="x", expand=True)

    def _tip(self, parent, text: str) -> None:
        box = ctk.CTkFrame(parent, fg_color=("#EFF6FF", "#1E3A5F"), corner_radius=8)
        box.pack(fill="x", pady=(4, 8), padx=2)
        ctk.CTkLabel(
            box, text=f"💡  {text}",
            font=ctk.CTkFont(size=11),
            text_color=("#1D4ED8", "#93C5FD"),
            anchor="w", justify="left",
            wraplength=555,
        ).pack(padx=12, pady=8, anchor="w")

    def _hotkey_row(self, parent, hotkey: str, description: str) -> None:
        row = ctk.CTkFrame(parent, fg_color=("#F9FAFB", "#2A2A2A"), corner_radius=6)
        row.pack(fill="x", pady=(2, 4), padx=2)
        ctk.CTkLabel(
            row, text=f"  {hotkey}  ",
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color=("#E5E7EB", "#374151"),
            corner_radius=4,
            width=170,
            anchor="w",
        ).pack(side="left", padx=(8, 0), pady=6)
        ctk.CTkLabel(
            row, text=description,
            font=ctk.CTkFont(size=11),
            anchor="w",
        ).pack(side="left", padx=10)

    def _faq(self, parent, question: str, answer: str) -> None:
        ctk.CTkLabel(
            parent, text=f"F:  {question}",
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="w", justify="left",
            wraplength=570,
        ).pack(fill="x", anchor="w", pady=(8, 1))
        ctk.CTkLabel(
            parent, text=f"A:  {answer}",
            font=ctk.CTkFont(size=11),
            text_color=("#374151", "#D1D5DB"),
            anchor="w", justify="left",
            wraplength=570,
        ).pack(fill="x", anchor="w", pady=(0, 2))
