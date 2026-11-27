# Copyright (c) 2026 Thorben Meier. MIT License.
"""
Settings window — equivalent to macOS SettingsContentView.
Opens as a modal dialog from the main window.
"""

import threading
import tkinter as tk
import customtkinter as ctk

from app_state import AppState
from services import credentials_service, paste_service
from services.local_transcription_service import MODELS as WHISPER_MODELS, cache_dir, is_model_cached
from services.audio_recorder import list_input_devices
from version import __version__


class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent, app_state: AppState):
        super().__init__(parent)
        self._app = app_state
        self.title("Blitzdiktat – Einstellungen")
        self.geometry("480x740")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.grab_set()
        self.focus_force()
        self.update_idletasks()
        paste_service.register_own_window(self.winfo_id())
        self._build()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(10, 0))
        ctk.CTkButton(
            header,
            text="📖  Handbuch",
            width=130,
            height=28,
            fg_color="transparent",
            border_width=1,
            border_color=("#D1D5DB", "#4B5563"),
            text_color=("#374151", "#D1D5DB"),
            hover_color=("#F3F4F6", "#374151"),
            command=self._open_help,
        ).pack(side="right")

        scroll = ctk.CTkScrollableFrame(self)
        scroll.pack(fill="both", expand=True, padx=16, pady=(8, 16))

        s = self._app.settings

        # ---- Darstellung ------------------------------------------
        self._section(scroll, "Darstellung")
        _appearance_map = {
            "System (automatisch)": "System",
            "Hell":                 "Light",
            "Dunkel":               "Dark",
        }
        self._appearance_map = _appearance_map
        _value_to_label = {v: k for k, v in _appearance_map.items()}
        current_appearance_label = _value_to_label.get(s.appearance_mode, "System (automatisch)")
        self._appearance_var = ctk.StringVar(value=current_appearance_label)
        ctk.CTkOptionMenu(
            scroll,
            values=list(_appearance_map.keys()),
            variable=self._appearance_var,
            width=220,
            command=self._on_appearance_change,
        ).pack(anchor="w", pady=(0, 12))

        # ---- Mikrofon -----------------------------------------------
        self._section(scroll, "Mikrofon")
        self._mic_devices: list[tuple[int, str]] = list_input_devices()
        _DEFAULT = "Standard (Systemstandard)"
        mic_labels = [_DEFAULT] + [name for _, name in self._mic_devices]

        saved_mic = s.selected_microphone
        current_mic = saved_mic if saved_mic in mic_labels else _DEFAULT

        self._mic_var = ctk.StringVar(value=current_mic)

        mic_row = ctk.CTkFrame(scroll, fg_color="transparent")
        mic_row.pack(fill="x", pady=(0, 4))

        self._mic_menu = ctk.CTkOptionMenu(
            mic_row,
            values=mic_labels,
            variable=self._mic_var,
            width=340,
            command=self._on_mic_change,
        )
        self._mic_menu.pack(side="left")

        ctk.CTkButton(
            mic_row,
            text="↺",
            width=36,
            height=32,
            fg_color="transparent",
            border_width=1,
            command=lambda: self._refresh_mics(_DEFAULT),
        ).pack(side="left", padx=(6, 0))

        # ---- Transkriptions-Backend --------------------------------
        self._section(scroll, "Transkription")

        self._backend_var = ctk.StringVar(
            value=s.transcription_backend
        )

        row_online = ctk.CTkFrame(scroll, fg_color="transparent")
        row_online.pack(fill="x", pady=1)
        ctk.CTkRadioButton(
            row_online,
            text="☁️  Online  —  OpenAI Whisper API",
            variable=self._backend_var,
            value="online",
            command=self._on_backend_change,
        ).pack(side="left")

        row_local = ctk.CTkFrame(scroll, fg_color="transparent")
        row_local.pack(fill="x", pady=1)
        ctk.CTkRadioButton(
            row_local,
            text="🔒  Lokal  —  faster-whisper (offline, kein API Key)",
            variable=self._backend_var,
            value="local",
            command=self._on_backend_change,
        ).pack(side="left")

        ctk.CTkLabel(scroll, text="Whisper-Modell (lokal)").pack(anchor="w", pady=(6, 0))

        model_labels = [m[1] for m in WHISPER_MODELS]
        model_names  = [m[0] for m in WHISPER_MODELS]
        current_label = next(
            (m[1] for m in WHISPER_MODELS if m[0] == s.local_whisper_model),
            model_labels[2],
        )
        self._model_var = ctk.StringVar(value=current_label)
        self._model_names = model_names
        self._model_labels = model_labels

        ctk.CTkOptionMenu(
            scroll,
            values=model_labels,
            variable=self._model_var,
            width=400,
            command=self._on_model_change,
        ).pack(anchor="w", pady=(2, 4))

        self._model_status = ctk.CTkLabel(
            scroll,
            text=self._model_status_text(s.local_whisper_model),
            font=ctk.CTkFont(size=11),
            text_color=("#6B7280", "#9CA3AF"),
        )
        self._model_status.pack(anchor="w")

        ctk.CTkLabel(
            scroll,
            text=f"📁 Speicherort: {cache_dir()}",
            font=ctk.CTkFont(size=10),
            text_color=("#9CA3AF", "#6B7280"),
            wraplength=440,
            justify="left",
        ).pack(anchor="w", pady=(2, 12))

        # ---- KI-Anbieter für die Textverarbeitung -------------------
        self._build_llm_provider_section(scroll, s)

        # ---- API Key -----------------------------------------------
        self._section(scroll, "OpenAI API Key")

        current_key = credentials_service.load_api_key() or ""
        self._api_entry = ctk.CTkEntry(
            scroll,
            placeholder_text="sk-...",
            show="•",
            width=400,
        )
        if current_key:
            self._api_entry.insert(0, current_key)
        self._api_entry.pack(anchor="w", pady=(0, 4))

        ctk.CTkButton(
            scroll,
            text="API Key speichern",
            width=180,
            command=self._save_api_key,
        ).pack(anchor="w", pady=(0, 12))

        # ---- OpenAI-Modelle ----------------------------------------
        from services.llm_service import DEFAULT_MODEL_FAST, DEFAULT_MODEL_QUALITY

        self._section(scroll, "OpenAI-Modelle")

        self._llm_std_fast = f"Standard ({DEFAULT_MODEL_FAST})"
        self._llm_std_quality = f"Standard ({DEFAULT_MODEL_QUALITY})"
        _llm_choices = ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt-4.1"]

        def _llm_values(saved: str, std_label: str) -> list[str]:
            # Per Hand in settings.json eingetragene Modelle bleiben wählbar.
            values = [std_label] + _llm_choices
            if saved and saved not in values:
                values.append(saved)
            return values

        ctk.CTkLabel(scroll, text="Schnelles Modell").pack(anchor="w")
        ctk.CTkLabel(
            scroll,
            text="Für Blitzdiktat+, Blitzdiktat :) und Vokabular-Extraktion.",
            font=ctk.CTkFont(size=11),
            text_color=("#6B7280", "#9CA3AF"),
        ).pack(anchor="w", pady=(0, 2))
        self._llm_fast_var = ctk.StringVar(
            value=s.openai_model_fast or self._llm_std_fast
        )
        ctk.CTkOptionMenu(
            scroll,
            values=_llm_values(s.openai_model_fast, self._llm_std_fast),
            variable=self._llm_fast_var,
            width=260,
            command=self._on_llm_fast_change,
        ).pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(scroll, text="Qualitätsmodell").pack(anchor="w")
        ctk.CTkLabel(
            scroll,
            text="Für Blitzdiktat Protokoll und Blitzdiktat $%&!.",
            font=ctk.CTkFont(size=11),
            text_color=("#6B7280", "#9CA3AF"),
        ).pack(anchor="w", pady=(0, 2))
        self._llm_quality_var = ctk.StringVar(
            value=s.openai_model_quality or self._llm_std_quality
        )
        ctk.CTkOptionMenu(
            scroll,
            values=_llm_values(s.openai_model_quality, self._llm_std_quality),
            variable=self._llm_quality_var,
            width=260,
            command=self._on_llm_quality_change,
        ).pack(anchor="w", pady=(0, 12))

        # ---- Sprache -----------------------------------------------
        self._section(scroll, "Sprache")
        self._lang_var = ctk.StringVar(value=s.language)
        lang_menu = ctk.CTkOptionMenu(
            scroll,
            values=["de", "en", "fr", "es", "it", "nl", "pl"],
            variable=self._lang_var,
            width=120,
        )
        lang_menu.pack(anchor="w", pady=(0, 12))

        # ---- Gelerntes Vokabular -----------------------------------
        from services import vocabulary_service
        self._section(scroll, "Gelerntes Vokabular")
        ctk.CTkLabel(
            scroll,
            text="Automatisch gelernte Begriffe — ein Begriff pro Zeile. "
                 "Direkt bearbeiten, manuell ergänzen oder einzelne Einträge löschen.",
            font=ctk.CTkFont(size=11),
            text_color=("#6B7280", "#9CA3AF"),
            wraplength=440,
            justify="left",
        ).pack(anchor="w", pady=(0, 4))

        self._vocab_box = ctk.CTkTextbox(scroll, width=400, height=150)
        self._vocab_box.insert("1.0", "\n".join(vocabulary_service.get_learned_terms()))
        self._vocab_box.pack(anchor="w", pady=(0, 6))

        _vocab_btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        _vocab_btn_row.pack(anchor="w", pady=(0, 12))
        ctk.CTkButton(
            _vocab_btn_row,
            text="Vokabular speichern",
            width=180,
            command=self._save_vocabulary,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            _vocab_btn_row,
            text="Alles löschen",
            fg_color="transparent",
            border_width=1,
            border_color=("#D1D5DB", "#4B5563"),
            text_color=("#374151", "#D1D5DB"),
            hover_color=("#F3F4F6", "#374151"),
            width=120,
            command=self._clear_vocabulary,
        ).pack(side="left")

        # ---- Hotkeys -----------------------------------------------
        self._section(scroll, "Tastenkürzel (z. B. ctrl+shift+r)")

        self._hk_transcription = self._hotkey_row(
            scroll, "Blitzdiktat", s.hotkey_transcription
        )
        self._hk_text_improver = self._hotkey_row(
            scroll, "Blitzdiktat+", s.hotkey_text_improver
        )
        self._hk_dampf = self._hotkey_row(
            scroll, "Blitzdiktat $%&!", s.hotkey_dampf_ablassen
        )
        self._hk_emoji = self._hotkey_row(
            scroll, "Blitzdiktat :)", s.hotkey_emoji_text
        )
        self._hk_protokoll = self._hotkey_row(
            scroll, "Blitzdiktat Protokoll", s.hotkey_protokoll
        )
        self._hk_notiz = self._hotkey_row(
            scroll, "Blitzdiktat Notiz", s.hotkey_notiz
        )

        # ---- Text-Verbesserung -------------------------------------
        self._section(scroll, "Blitzdiktat+ Einstellungen")

        ctk.CTkLabel(scroll, text="Ton").pack(anchor="w")
        self._tone_var = ctk.StringVar(value=s.text_improvement.tone)
        ctk.CTkOptionMenu(
            scroll,
            values=["formal", "neutral", "casual"],
            variable=self._tone_var,
            width=160,
        ).pack(anchor="w", pady=(0, 6))

        ctk.CTkLabel(scroll, text="Kontext (optional)").pack(anchor="w")
        self._context_entry = ctk.CTkEntry(scroll, width=400, placeholder_text="z. B. E-Mail an Kunden")
        self._context_entry.insert(0, s.text_improvement.context)
        self._context_entry.pack(anchor="w", pady=(0, 6))

        ctk.CTkLabel(scroll, text="Eigennamen / Fachbegriffe (Komma-getrennt)").pack(anchor="w")
        self._terms_entry = ctk.CTkEntry(scroll, width=400, placeholder_text="OpenAI, Blitzdiktat, ...")
        self._terms_entry.insert(0, ", ".join(s.text_improvement.custom_terms))
        self._terms_entry.pack(anchor="w", pady=(0, 6))

        ctk.CTkLabel(scroll, text="Eigener System-Prompt (leer = Standard)").pack(anchor="w")
        self._prompt_box = ctk.CTkTextbox(scroll, width=400, height=80)
        self._prompt_box.insert("1.0", s.text_improvement.system_prompt)
        self._prompt_box.pack(anchor="w", pady=(0, 12))

        # ---- Dampf ablassen ----------------------------------------
        self._section(scroll, "Blitzdiktat $%&! Einstellungen")

        ctk.CTkLabel(scroll, text="System-Prompt (leer = Standard)").pack(anchor="w")
        self._dampf_prompt = ctk.CTkTextbox(scroll, width=400, height=80)
        self._dampf_prompt.insert("1.0", s.dampf_ablassen.system_prompt)
        self._dampf_prompt.pack(anchor="w", pady=(0, 12))

        # ---- Emoji -------------------------------------------------
        self._section(scroll, "Blitzdiktat :) Einstellungen")

        ctk.CTkLabel(scroll, text="Emoji-Dichte").pack(anchor="w")
        self._emoji_var = ctk.StringVar(value=s.emoji_text.emoji_density)
        ctk.CTkOptionMenu(
            scroll,
            values=["wenig", "mittel", "viel"],
            variable=self._emoji_var,
            width=160,
        ).pack(anchor="w", pady=(0, 12))

        # ---- Protokoll ---------------------------------------------
        self._section(scroll, "Blitzdiktat Protokoll Einstellungen")

        ctk.CTkLabel(
            scroll,
            text="Eigener System-Prompt (leer = Standard)",
        ).pack(anchor="w")
        ctk.CTkLabel(
            scroll,
            text="Leer lassen um den eingebauten Protokoll-Prompt zu verwenden.",
            font=ctk.CTkFont(size=10),
            text_color=("#9CA3AF", "#6B7280"),
            wraplength=440,
            justify="left",
        ).pack(anchor="w", pady=(0, 4))
        self._protokoll_prompt = ctk.CTkTextbox(scroll, width=400, height=120)
        self._protokoll_prompt.insert("1.0", s.protokoll.system_prompt)
        self._protokoll_prompt.pack(anchor="w", pady=(0, 12))

        # ---- Save button -------------------------------------------
        ctk.CTkButton(
            scroll,
            text="Einstellungen speichern",
            command=self._save,
            height=40,
        ).pack(fill="x", pady=(8, 0))

        # ---- Über ------------------------------------------------------
        ctk.CTkFrame(scroll, height=1, fg_color=("#E5E7EB", "#374151")).pack(
            fill="x", pady=(12, 4)
        )
        ctk.CTkLabel(
            scroll,
            text=f"© 2026 Thorben Meier  ·  MIT License  ·  v{__version__}",
            font=ctk.CTkFont(size=10),
            text_color=("#9CA3AF", "#6B7280"),
        ).pack(pady=(0, 8))

    def _build_llm_provider_section(self, scroll, s) -> None:
        """Umschalter: Textverarbeitung über OpenAI oder einen eigenen Server."""
        from services import llm_service

        self._section(scroll, "KI für die Textverarbeitung")
        ctk.CTkLabel(
            scroll,
            text="Für Blitzdiktat+, Blitzdiktat $%&!, Blitzdiktat :), Protokoll "
                 "und das gelernte Vokabular.",
            font=ctk.CTkFont(size=11),
            text_color=("#6B7280", "#9CA3AF"),
            wraplength=440,
            justify="left",
        ).pack(anchor="w", pady=(0, 4))

        # Einfache Ansicht: Blitzdiktat richtet die lokale KI selbst ein. Alles
        # Technische (Anbieter, Adresse, Modell, Schlüssel) steht unter "Erweitert".
        self._auto_status = ctk.CTkLabel(
            scroll, text=self._auto_status_text(), font=ctk.CTkFont(size=12),
            wraplength=440, justify="left",
        )
        self._auto_status.pack(anchor="w", pady=(0, 4))
        auto_row = ctk.CTkFrame(scroll, fg_color="transparent")
        auto_row.pack(anchor="w", pady=(0, 4))
        ctk.CTkButton(
            auto_row, text="Automatisch einrichten", width=190, command=self._run_auto_setup,
        ).pack(side="left", padx=(0, 6))
        self._adv_toggle = ctk.CTkButton(
            auto_row, text="Erweitert ▾", width=120, command=self._toggle_advanced,
            fg_color="transparent", border_width=1,
            border_color=("#D1D5DB", "#4B5563"), text_color=("#374151", "#D1D5DB"),
        )
        self._adv_toggle.pack(side="left")
        self._adv = ctk.CTkFrame(scroll, fg_color="transparent")
        self._adv_open = False
        self._tick_auto_status()
        scroll = self._adv          # alles Weitere gehört zur eingeklappten Ansicht

        self._provider_var = ctk.StringVar(value=s.llm_provider)
        for value, text in (
            (llm_service.PROVIDER_OPENAI, "☁️  Online  —  OpenAI (API Key nötig)"),
            (llm_service.PROVIDER_CUSTOM, "🖥️  Eigener Server  —  z. B. LM Studio (lokal, offline)"),
        ):
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", pady=1)
            ctk.CTkRadioButton(
                row, text=text, variable=self._provider_var, value=value,
                command=self._on_provider_change,
            ).pack(side="left")

        ctk.CTkLabel(scroll, text="Server-Adresse").pack(anchor="w", pady=(8, 0))
        self._custom_url_entry = ctk.CTkEntry(
            scroll, width=400, placeholder_text=llm_service.DEFAULT_CUSTOM_BASE_URL,
        )
        self._custom_url_entry.insert(0, s.custom_llm_base_url)
        self._custom_url_entry.pack(anchor="w", pady=(0, 6))

        ctk.CTkLabel(scroll, text="Modell").pack(anchor="w")
        self._custom_model_var = ctk.StringVar(value=s.custom_llm_model)
        self._custom_model_box = ctk.CTkComboBox(
            scroll,
            values=[s.custom_llm_model] if s.custom_llm_model else [""],
            variable=self._custom_model_var,
            width=400,
        )
        self._custom_model_box.pack(anchor="w", pady=(0, 6))

        ctk.CTkLabel(scroll, text="API Key des Servers (optional, LM Studio braucht keinen)").pack(anchor="w")
        self._custom_key_entry = ctk.CTkEntry(scroll, show="•", width=400)
        current_custom_key = credentials_service.load_custom_api_key() or ""
        if current_custom_key:
            self._custom_key_entry.insert(0, current_custom_key)
        self._custom_key_entry.pack(anchor="w", pady=(0, 6))

        self._custom_test_btn = ctk.CTkButton(
            scroll,
            text="Verbinden und speichern",
            width=200,
            command=self._connect_custom_server,
        )
        self._custom_test_btn.pack(anchor="w", pady=(0, 4))

        self._custom_status = ctk.CTkLabel(
            scroll,
            text=self._custom_status_idle_text(),
            font=ctk.CTkFont(size=11),
            text_color=("#6B7280", "#9CA3AF"),
            wraplength=440,
            justify="left",
        )
        self._custom_status.pack(anchor="w")

        from features.ui.local_ai_panel import LocalAiPanel
        LocalAiPanel(
            scroll, self._app,
            get_url=lambda: llm_service.normalize_base_url(self._custom_url_entry.get())
            or llm_service.DEFAULT_CUSTOM_BASE_URL,
            get_key=lambda: self._custom_key_entry.get().strip(),
            on_activate=self._activate_local_model,
            on_models=self._set_model_choices,
        ).pack(anchor="w", pady=(6, 0))
        self._refresh_models_quietly()

        ctk.CTkLabel(
            scroll,
            text="Hinweis: Blitzdiktat lädt das gewählte Modell mit 8192 Tokens Kontextlänge, "
                 "damit lange Protokolle nicht abgeschnitten werden. Auf dem Prozessor dauert ein "
                 "Diktat lokal etwa 10–25 Sekunden, ein Protokoll auch Minuten.",
            font=ctk.CTkFont(size=10),
            text_color=("#9CA3AF", "#6B7280"),
            wraplength=440,
            justify="left",
        ).pack(anchor="w", pady=(2, 12))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _section(self, parent, title: str) -> None:
        ctk.CTkLabel(
            parent,
            text=title,
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", pady=(8, 2))
        ctk.CTkFrame(parent, height=1, fg_color=("#E5E7EB", "#374151")).pack(
            fill="x", pady=(0, 6)
        )

    def _hotkey_row(self, parent, label: str, default: str) -> ctk.CTkEntry:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=2)
        ctk.CTkLabel(row, text=label, width=140, anchor="w").pack(side="left")
        entry = ctk.CTkEntry(row, width=200, placeholder_text="ctrl+shift+r")
        entry.insert(0, default)
        entry.pack(side="left")
        return entry

    def _open_help(self) -> None:
        from features.ui.help_window import HelpWindow
        HelpWindow(self, settings=self._app.settings)

    def _save_vocabulary(self) -> None:
        from services import vocabulary_service
        raw = self._vocab_box.get("1.0", "end").strip()
        terms = [t.strip() for t in raw.splitlines() if t.strip()]
        seen: set[str] = set()
        unique: list[str] = []
        for t in terms:
            if t.lower() not in seen:
                seen.add(t.lower())
                unique.append(t)
        vocabulary_service.clear()
        vocabulary_service.add_terms(unique)
        self._show_toast(f"{len(unique)} Begriff{'e' if len(unique) != 1 else ''} gespeichert ✓")

    def _clear_vocabulary(self) -> None:
        from services import vocabulary_service
        vocabulary_service.clear()
        self._vocab_box.delete("1.0", "end")
        self._show_toast("Vokabular gelöscht ✓")

    def _on_appearance_change(self, label: str) -> None:
        mode = self._appearance_map.get(label, "System")
        ctk.set_appearance_mode(mode)
        self._app.settings.appearance_mode = mode
        self._app.save_settings()

    def _on_mic_change(self, label: str) -> None:
        _DEFAULT = "Standard (Systemstandard)"
        self._app.settings.selected_microphone = "" if label == _DEFAULT else label
        self._app.save_settings()

    def _refresh_mics(self, default_label: str) -> None:
        self._mic_devices = list_input_devices()
        labels = [default_label] + [name for _, name in self._mic_devices]
        self._mic_menu.configure(values=labels)
        if self._mic_var.get() not in labels:
            self._mic_var.set(default_label)
            self._app.settings.selected_microphone = ""
            self._app.save_settings()

    def _model_status_text(self, model_name: str) -> str:
        if is_model_cached(model_name):
            return f"✅  {model_name} ist lokal gespeichert"
        return f"⬇️  {model_name} wird beim ersten Start automatisch heruntergeladen (~{'75 MB' if model_name == 'tiny' else '150 MB' if model_name == 'base' else '500 MB' if model_name == 'small' else '1.5 GB' if model_name == 'medium' else '3 GB'})"

    def _on_backend_change(self) -> None:
        self._app.settings.transcription_backend = self._backend_var.get()
        self._app.save_settings()

    def _on_model_change(self, label: str) -> None:
        idx = self._model_labels.index(label)
        model_name = self._model_names[idx]
        previous = self._app.settings.local_whisper_model
        self._app.settings.local_whisper_model = model_name
        self._app.save_settings()
        if previous and previous != model_name:
            # Altes Modell aus dem RAM werfen — sonst liegen z. B. medium
            # (1,5 GB) und large-v3 (3 GB) gleichzeitig im Speicher.
            from services.local_transcription_service import evict_model
            evict_model(previous)
        self._model_status.configure(text=self._model_status_text(model_name))

    def _on_llm_fast_change(self, label: str) -> None:
        self._app.settings.openai_model_fast = (
            "" if label == self._llm_std_fast else label
        )
        self._app.save_settings()

    def _on_llm_quality_change(self, label: str) -> None:
        self._app.settings.openai_model_quality = (
            "" if label == self._llm_std_quality else label
        )
        self._app.save_settings()

    # ---- Eigener KI-Server ---------------------------------------------

    def _custom_status_idle_text(self) -> str:
        s = self._app.settings
        if s.llm_provider != "custom":
            return "Eigener Server ist nicht aktiv – die Textverarbeitung läuft über OpenAI."
        if not s.custom_llm_model:
            return "⚠️  Noch kein Modell gewählt: „Verbinden und speichern“ klicken."
        return f"Aktiv: {s.custom_llm_model}"

    def _on_provider_change(self) -> None:
        self._app.settings.llm_provider = self._provider_var.get()
        self._app.settings.local_ai_auto = False      # manuelle Wahl: Automatik bleibt aus
        self._app.save_settings()
        self._custom_status.configure(
            text=self._custom_status_idle_text(), text_color=("#6B7280", "#9CA3AF"),
        )

    def _connect_custom_server(self) -> None:
        """Fragt den Server nach seinen Modellen und speichert Adresse, Modell und Key."""
        from services import llm_service

        url = llm_service.normalize_base_url(self._custom_url_entry.get()) \
            or llm_service.DEFAULT_CUSTOM_BASE_URL
        key = self._custom_key_entry.get().strip()
        self._custom_test_btn.configure(state="disabled")
        self._custom_status.configure(
            text="Verbinde … (startet LM Studio bei Bedarf, das kann eine Minute dauern)",
            text_color=("#6B7280", "#9CA3AF"),
        )
        result: dict = {}

        def work() -> None:
            from services import local_server
            try:
                try:
                    models = llm_service.list_models(url, key)
                except Exception:
                    # LM Studio auf diesem Rechner: Server selbst starten
                    # (auch wenn ein früherer Versuch gerade gescheitert ist).
                    started = local_server.start_local_server(url, force=True)
                    if not started.ok:
                        result["reason"] = started.reason
                        raise
                    models = llm_service.list_models(url, key)
                result["models"] = models
            except Exception as e:  # Anzeige übernimmt der Hauptthread
                result["error"] = e

        def poll() -> None:
            if not self.winfo_exists():
                return
            if not result:
                self.after(100, poll)
                return
            self._custom_test_btn.configure(state="normal")
            self._custom_connect_done(url, key, result)

        threading.Thread(target=work, daemon=True).start()
        self.after(100, poll)

    def _auto_status_text(self) -> str:
        from services import local_ai_setup
        s = self._app.settings
        st = local_ai_setup.status
        if st.state == local_ai_setup.WORKING:
            return f"⏳  {st.message}"
        if st.state == local_ai_setup.FAILED:
            return f"⚠️  {st.message}"
        if s.llm_provider != "custom":
            return "☁️  Die Textverarbeitung läuft online über OpenAI."
        if not s.local_ai_auto:
            return (f"🛠️  Manuell eingestellt: {s.custom_llm_model or 'kein Modell'}. "
                    "„Automatisch einrichten“ übergibt wieder an Blitzdiktat.")
        if st.state == local_ai_setup.READY:
            return f"✅  {st.message}"
        return f"🖥️  Lokale KI wird automatisch verwaltet ({s.custom_llm_model or 'noch kein Modell'})."

    def _tick_auto_status(self) -> None:
        if not self.winfo_exists():
            return
        self._auto_status.configure(text=self._auto_status_text())
        self.after(1000, self._tick_auto_status)

    def _run_auto_setup(self) -> None:
        self._app.settings.local_ai_auto = True
        self._app.save_ai_settings()
        self._app.start_local_ai_setup(force=True)
        self._auto_status.configure(text="⏳  Prüfe die lokale KI …")

    def _toggle_advanced(self) -> None:
        self._adv_open = not self._adv_open
        if self._adv_open:
            self._adv.pack(anchor="w", fill="x", after=self._adv_toggle.master)
            self._adv_toggle.configure(text="Erweitert ▴")
        else:
            self._adv.pack_forget()
            self._adv_toggle.configure(text="Erweitert ▾")

    def _set_model_choices(self, names: list[str]) -> None:
        """Trägt die Modelle des Servers in die Auswahlliste ein."""
        if names:
            self._custom_model_box.configure(values=names)

    def _activate_local_model(self, model_id: str) -> None:
        """Schaltet die Textverarbeitung auf das gewählte Modell des eigenen Servers."""
        from services import llm_service
        s = self._app.settings
        s.llm_provider = llm_service.PROVIDER_CUSTOM
        s.custom_llm_model = model_id
        s.local_ai_auto = False                  # manuelle Wahl: Automatik bleibt aus
        s.custom_llm_base_url = llm_service.normalize_base_url(self._custom_url_entry.get()) \
            or llm_service.DEFAULT_CUSTOM_BASE_URL
        self._provider_var.set(llm_service.PROVIDER_CUSTOM)
        self._custom_model_var.set(model_id)
        self._app.save_settings()
        self._custom_status.configure(
            text=self._custom_status_idle_text(), text_color=("#6B7280", "#9CA3AF"),
        )

    def _refresh_models_quietly(self) -> None:
        """Füllt die Modellliste beim Öffnen – ohne den Server zu starten oder Meldungen."""
        if self._app.settings.llm_provider != "custom":
            return
        from services import llm_service
        url = self._app.settings.custom_llm_base_url
        key = credentials_service.load_custom_api_key() or ""
        result: dict = {}

        def work() -> None:
            try:
                result["models"] = llm_service.list_models(url, key, timeout=3)
            except Exception:
                result["models"] = []

        def poll() -> None:
            if not self.winfo_exists():
                return
            if "models" not in result:
                self.after(200, poll)
                return
            self._set_model_choices(result["models"])
            if self._app.heal_local_model(result["models"]):
                self._custom_model_var.set(self._app.settings.custom_llm_model)
                self._custom_status.configure(
                    text=self._custom_status_idle_text(), text_color=("#6B7280", "#9CA3AF"),
                )

        threading.Thread(target=work, daemon=True).start()
        self.after(200, poll)

    def _custom_connect_done(self, url: str, key: str, result: dict) -> None:
        s = self._app.settings
        # Adresse und Key auch bei Fehlschlag merken – der Server kann später starten.
        s.custom_llm_base_url = url
        s.local_ai_auto = False                  # manuelle Wahl: Automatik bleibt aus
        self._custom_url_entry.delete(0, "end")
        self._custom_url_entry.insert(0, url)
        if key:
            credentials_service.save_custom_api_key(key)
        else:
            credentials_service.delete_custom_api_key()

        if "error" in result:
            s.custom_llm_model = self._custom_model_var.get().strip()
            self._app.save_settings()
            reason = result.get("reason", "")
            self._custom_status.configure(
                text="❌  Server nicht erreichbar" + (f": {reason}" if reason else ".")
                     + " Die Modell-Liste ist deshalb noch leer. Blitzdiktat versucht den "
                       "Start bei jedem Diktat erneut; hilft das nicht, in LM Studio unter "
                       "„Developer“ den Server einschalten.",
                text_color="#EF4444",
            )
            return

        models = result["models"]
        chosen = self._custom_model_var.get().strip()
        from services import model_catalog
        chosen = model_catalog.resolve_model(chosen, models) or chosen
        if models and chosen not in models:
            chosen = models[0]
        self._custom_model_box.configure(values=models or [""])
        self._custom_model_var.set(chosen)
        s.custom_llm_model = chosen
        self._app.save_settings()
        if not models:
            self._custom_status.configure(
                text="⚠️  Verbunden, aber der Server meldet kein Modell. Bitte dort eines laden.",
                text_color="#F59E0B",
            )
            return
        aktiv = "" if s.llm_provider == "custom" else "  (oben „Eigener Server“ wählen, um ihn zu nutzen)"
        self._custom_status.configure(
            text=f"✅  Verbunden – {len(models)} Modell{'e' if len(models) != 1 else ''} gefunden. "
                 f"Gewählt: {chosen}{aktiv}",
            text_color=("#16A34A", "#22C55E"),
        )

    def _save_api_key(self) -> None:
        key = self._api_entry.get().strip()
        if key:
            credentials_service.save_api_key(key)
            self._show_toast("API Key gespeichert ✓")
        else:
            credentials_service.delete_api_key()
            self._show_toast("API Key gelöscht")

    def _save(self) -> None:
        s = self._app.settings

        s.language = self._lang_var.get()

        s.hotkey_transcription = self._hk_transcription.get().strip()
        s.hotkey_text_improver = self._hk_text_improver.get().strip()
        s.hotkey_dampf_ablassen = self._hk_dampf.get().strip()
        s.hotkey_emoji_text = self._hk_emoji.get().strip()
        s.hotkey_protokoll = self._hk_protokoll.get().strip()
        s.hotkey_notiz = self._hk_notiz.get().strip()

        s.text_improvement.tone = self._tone_var.get()
        s.text_improvement.context = self._context_entry.get().strip()
        raw_terms = self._terms_entry.get().strip()
        s.text_improvement.custom_terms = [
            t.strip() for t in raw_terms.split(",") if t.strip()
        ]
        s.text_improvement.system_prompt = self._prompt_box.get("1.0", "end").strip()

        s.appearance_mode = self._appearance_map.get(self._appearance_var.get(), "System")
        ctk.set_appearance_mode(s.appearance_mode)

        s.dampf_ablassen.system_prompt = self._dampf_prompt.get("1.0", "end").strip()
        s.emoji_text.emoji_density = self._emoji_var.get()
        s.protokoll.system_prompt = self._protokoll_prompt.get("1.0", "end").strip()

        # Eigener KI-Server: getippte Adresse/Modell auch ohne Verbindungstest übernehmen.
        from services import llm_service
        s.llm_provider = self._provider_var.get()
        s.custom_llm_base_url = (
            llm_service.normalize_base_url(self._custom_url_entry.get())
            or llm_service.DEFAULT_CUSTOM_BASE_URL
        )
        s.custom_llm_model = self._custom_model_var.get().strip()

        # Kein Neustart nötig: save_settings() bindet die Hotkeys live neu,
        # alle übrigen Einstellungen werden beim nächsten Workflow-Start
        # gelesen. Der frühere os.execv-Neustart zerlegte zudem Pfade mit
        # Leerzeichen (C:\Program Files\...) und ließ Tray-Icon/Listener
        # verwaist zurück.
        self._app.save_settings()
        self._show_toast("Gespeichert ✓")
        self.after(1200, self.destroy)

    def _show_toast(self, msg: str) -> None:
        toast = ctk.CTkLabel(
            self,
            text=msg,
            fg_color=("#22C55E", "#166534"),
            corner_radius=8,
            font=ctk.CTkFont(size=12),
            padx=12,
            pady=6,
        )
        toast.place(relx=0.5, rely=0.95, anchor="center")
        self.after(2000, toast.destroy)
