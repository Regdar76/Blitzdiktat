# Copyright (c) 2026 Thorben Meier. MIT License.
"""
Main popup window — equivalent to the macOS popover.
Frameless, always-on-top, draggable via title bar.
Bleibt offen bis der Nutzer explizit ✕ klickt.
"""

import os
import threading
import tkinter as tk
import customtkinter as ctk

from app_state import AppState
from features.workflows.base_workflow import WorkflowPhase, WorkflowType
from services import paste_service
from version import __version__
from services.audio_recorder import recordings_dir
from services.transcript_store import transcripts_dir

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

_WINDOW_W = 300
_WINDOW_H = 600
_PAD = 12
_BTN_H = 36          # inner button height (reduced; subtitle adds ~26 px per row)


def _lighten(hex_color: str, amount: int = 18) -> str:
    """Return a slightly lighter version of a hex colour (for hover effect)."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return "#{:02X}{:02X}{:02X}".format(
        min(255, r + amount), min(255, g + amount), min(255, b + amount)
    )


def _dim(hex_color: str) -> str:
    """Return a muted/dimmed version of a hex colour (for disabled state)."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r = int(r * 0.42 + 105 * 0.58)
    g = int(g * 0.42 + 105 * 0.58)
    b = int(b * 0.42 + 105 * 0.58)
    return "#{:02X}{:02X}{:02X}".format(r, g, b)


class MainWindow:
    def __init__(self, app_state: AppState):
        self._app = app_state
        self._root = ctk.CTk()
        self._root.title("Blitzdiktat")
        self._root.geometry(f"{_WINDOW_W}x{_WINDOW_H}")
        self._root.resizable(False, False)
        self._root.overrideredirect(True)   # kein nativer Rahmen
        self._root.attributes("-topmost", True)
        self._root.withdraw()

        # Drag-Zustand
        self._drag_x = 0
        self._drag_y = 0

        self._build_ui()
        app_state.subscribe(self._on_state_changed)

        # Register own HWND so the foreground tracker ignores this window,
        # and start the tracker so button clicks find the correct target.
        self._root.update_idletasks()          # ensure HWND is assigned
        paste_service.register_own_window(self._root.winfo_id())
        paste_service.start_foreground_tracker()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def show(self) -> None:
        self._root.after(0, self._do_show)

    def hide(self) -> None:
        self._root.after(0, self._root.withdraw)

    def quit(self) -> None:
        self._root.after(0, self._root.destroy)

    def mainloop(self) -> None:
        self._root.mainloop()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        self._frame = ctk.CTkFrame(self._root, corner_radius=12)
        self._frame.pack(fill="both", expand=True, padx=1, pady=1)

        # ---- Titelleiste (auch Drag-Handle) -------------------------
        title_bar = ctk.CTkFrame(self._frame, fg_color="transparent", cursor="fleur")
        title_bar.pack(fill="x", padx=_PAD, pady=(_PAD, 4))

        title_label = ctk.CTkLabel(
            title_bar,
            text="⚡ Blitzdiktat",
            font=ctk.CTkFont(size=15, weight="bold"),
            cursor="fleur",
        )
        title_label.pack(side="left")

        version_label = ctk.CTkLabel(
            title_bar,
            text=f"v{__version__}",
            font=ctk.CTkFont(size=10),
            text_color=("#9CA3AF", "#9B9BA0"),
            cursor="fleur",
        )
        version_label.pack(side="left", padx=(6, 0))

        close_btn = ctk.CTkButton(
            title_bar,
            text="✕",
            width=28,
            height=28,
            fg_color="transparent",
            hover_color=("#D1D5DB", "#374151"),
            cursor="arrow",
            command=self.hide,
        )
        close_btn.pack(side="right")

        # Drag-Bindings nur auf Titelleiste und Label
        for widget in (title_bar, title_label, version_label):
            widget.bind("<ButtonPress-1>",   self._drag_start)
            widget.bind("<B1-Motion>",       self._drag_move)

        # ---- Status-Badge -------------------------------------------
        self._status_label = ctk.CTkLabel(
            self._frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=("#6B7280", "#9CA3AF"),
            wraplength=_WINDOW_W - _PAD * 2,
            justify="left",
        )
        self._status_label.pack(padx=_PAD, pady=(0, 6), anchor="w")

        # ---- Workflow-Buttons ---------------------------------------
        workflow_frame = ctk.CTkFrame(self._frame, fg_color="transparent")
        workflow_frame.pack(fill="x", padx=_PAD, pady=(0, 8))

        self._wf_buttons:     dict[WorkflowType, ctk.CTkButton] = {}
        self._wf_containers:  dict[WorkflowType, ctk.CTkFrame]  = {}
        self._wf_subtitles:   dict[WorkflowType, ctk.CTkLabel]  = {}
        self._import_btn:     ctk.CTkButton | None               = None

        for wtype, emoji in [
            (WorkflowType.TRANSCRIPTION,  "🎙️"),
            (WorkflowType.TEXT_IMPROVER,  "✨"),
            (WorkflowType.DAMPF_ABLASSEN, "🔥"),
            (WorkflowType.EMOJI_TEXT,     "😊"),
            (WorkflowType.PROTOKOLL,      "📋"),
        ]:
            color = wtype.color
            hover = _lighten(color)

            # Coloured outer frame — acts as visual button background
            container = ctk.CTkFrame(
                workflow_frame,
                fg_color=color,
                corner_radius=8,
            )
            container.pack(fill="x", pady=2)

            # Main button (transparent on the coloured frame)
            if wtype == WorkflowType.PROTOKOLL:
                btn_row = ctk.CTkFrame(container, fg_color="transparent")
                btn_row.pack(fill="x")
                btn = ctk.CTkButton(
                    btn_row,
                    text=f"{emoji}  {self._app.workflow_display_name(wtype)}",
                    height=_BTN_H,
                    anchor="w",
                    fg_color="transparent",
                    hover_color=hover,
                    text_color="white",
                    text_color_disabled="#D0D0D0",
                    font=ctk.CTkFont(size=13, weight="bold"),
                    corner_radius=8,
                    command=lambda t=wtype: self._on_workflow_click(t),
                )
                btn.pack(side="left", fill="x", expand=True)
                self._import_btn = ctk.CTkButton(
                    btn_row,
                    text="📂",
                    width=36,
                    height=_BTN_H,
                    fg_color="transparent",
                    hover_color=hover,
                    text_color="white",
                    text_color_disabled="#D0D0D0",
                    font=ctk.CTkFont(size=14),
                    corner_radius=8,
                    command=self._on_import_click,
                )
                self._import_btn.pack(side="right", padx=(0, 4))
            else:
                btn = ctk.CTkButton(
                    container,
                    text=f"{emoji}  {self._app.workflow_display_name(wtype)}",
                    height=_BTN_H,
                    anchor="w",
                    fg_color="transparent",
                    hover_color=hover,
                    text_color="white",
                    text_color_disabled="#D0D0D0",
                    font=ctk.CTkFont(size=13, weight="bold"),
                    corner_radius=8,
                    command=lambda t=wtype: self._on_workflow_click(t),
                )
                btn.pack(fill="x")

            # Subtitle label
            sub = ctk.CTkLabel(
                container,
                text=self._subtitle(wtype),
                font=ctk.CTkFont(size=10),
                text_color="#E8E8E8",
                anchor="w",
            )
            sub.pack(fill="x", padx=10, pady=(0, 6))
            # Clicking the subtitle row also triggers the workflow
            sub.bind(
                "<Button-1>",
                lambda e, t=wtype: self._on_workflow_click(t)
                    if self._wf_buttons[t].cget("state") == "normal" else None,
            )

            self._wf_buttons[wtype]    = btn
            self._wf_containers[wtype] = container
            self._wf_subtitles[wtype]  = sub

        # ---- Trennlinie ---------------------------------------------
        ctk.CTkFrame(self._frame, height=1, fg_color=("#E5E7EB", "#374151")).pack(
            fill="x", padx=_PAD, pady=4
        )

        # ---- Buttons unten (Audioaufnahmen + Einstellungen) ---------
        bottom = ctk.CTkFrame(self._frame, fg_color="transparent")
        bottom.pack(fill="x", padx=_PAD, pady=(0, _PAD))

        ctk.CTkButton(
            bottom,
            text="📂  Audioaufnahmen",
            height=34,
            fg_color="transparent",
            border_width=1,
            border_color=("#D1D5DB", "#4B5563"),
            text_color=("#374151", "#D1D5DB"),
            command=self._open_recordings_folder,
        ).pack(fill="x", pady=(0, 4))

        ctk.CTkButton(
            bottom,
            text="📄  Transkriptionen",
            height=34,
            fg_color="transparent",
            border_width=1,
            border_color=("#D1D5DB", "#4B5563"),
            text_color=("#374151", "#D1D5DB"),
            command=self._open_transcripts_folder,
        ).pack(fill="x", pady=(0, 4))

        settings_row = ctk.CTkFrame(bottom, fg_color="transparent")
        settings_row.pack(fill="x")

        ctk.CTkButton(
            settings_row,
            text="⚙️  Einstellungen",
            height=34,
            fg_color="transparent",
            border_width=1,
            border_color=("#D1D5DB", "#4B5563"),
            text_color=("#374151", "#D1D5DB"),
            command=self._open_settings,
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))

        ctk.CTkButton(
            settings_row,
            text="ⓘ",
            width=34,
            height=34,
            fg_color="transparent",
            border_width=1,
            border_color=("#D1D5DB", "#4B5563"),
            text_color=("#374151", "#D1D5DB"),
            font=ctk.CTkFont(size=15),
            command=self._open_help,
        ).pack(side="right")

        self._update_ui()

    # ------------------------------------------------------------------
    # Drag-Logik
    # ------------------------------------------------------------------

    def _drag_start(self, event: tk.Event) -> None:
        self._drag_x = event.x_root - self._root.winfo_x()
        self._drag_y = event.y_root - self._root.winfo_y()

    def _drag_move(self, event: tk.Event) -> None:
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self._root.geometry(f"+{x}+{y}")

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _subtitle(self, wtype: WorkflowType) -> str:
        """Subtitle text with hotkey badge, e.g. 'Sprache rein. Text raus.  ·  Ctrl+Shift+R'"""
        s = self._app.settings
        hk_raw = {
            WorkflowType.TRANSCRIPTION:  s.hotkey_transcription,
            WorkflowType.TEXT_IMPROVER:  s.hotkey_text_improver,
            WorkflowType.DAMPF_ABLASSEN: s.hotkey_dampf_ablassen,
            WorkflowType.EMOJI_TEXT:     s.hotkey_emoji_text,
            WorkflowType.PROTOKOLL:      s.hotkey_protokoll,
        }.get(wtype, "")
        if hk_raw:
            hk = "+".join(p.capitalize() for p in hk_raw.split("+"))
            return f"{wtype.subtitle}  ·  {hk}"
        return wtype.subtitle

    def _on_import_click(self) -> None:
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="Audiodatei oder Transkript auswählen",
            filetypes=[
                ("Unterstützte Dateien", "*.wav *.mp3 *.m4a *.ogg *.flac *.txt *.md"),
                ("Audiodateien", "*.wav *.mp3 *.m4a *.ogg *.flac"),
                ("Textdateien", "*.txt *.md"),
                ("Alle Dateien", "*.*"),
            ],
            parent=self._root,
        )
        if not path:
            return
        self._app.capture_target_window()
        self._app.import_file_for_protokoll(path)

    def _on_workflow_click(self, wtype: WorkflowType) -> None:
        wf = self._app.active_workflow
        if wf and wf.workflow_type == wtype and wf.is_recording:
            self._app.stop_workflow()
        else:
            self._app.capture_target_window()
            self._app.start_workflow(wtype)

    def _open_recordings_folder(self) -> None:
        os.startfile(recordings_dir())

    def _open_transcripts_folder(self) -> None:
        os.startfile(transcripts_dir())

    def _open_settings(self) -> None:
        from features.ui.settings_window import SettingsWindow
        SettingsWindow(self._root, self._app)   # kein hide() mehr

    def _open_help(self) -> None:
        from features.ui.help_window import HelpWindow
        HelpWindow(self._root, settings=self._app.settings)

    def _on_state_changed(self, state: AppState) -> None:
        self._root.after(0, self._update_ui)

    # ------------------------------------------------------------------
    # UI-Updates (immer im Main-Thread via root.after)
    # ------------------------------------------------------------------

    def _update_ui(self) -> None:
        wf = self._app.active_workflow
        phase = wf.state.phase if wf else WorkflowPhase.IDLE

        if phase == WorkflowPhase.RECORDING:
            self._status_label.configure(
                text=f"🔴  {wf.state.status_text}",
                text_color="#EF4444",
            )
        elif phase == WorkflowPhase.PROCESSING:
            self._status_label.configure(
                text=f"⏳  {wf.state.status_text}",
                text_color="#F59E0B",
            )
        elif phase == WorkflowPhase.DONE:
            self._status_label.configure(
                text="✅  Eingefügt",
                text_color="#22C55E",
            )
        elif phase == WorkflowPhase.ERROR:
            raw = wf.state.error_text if wf else ""
            clean = raw.split("\n")[0].strip()
            if len(clean) > 90:
                clean = clean[:87] + "..."
            self._status_label.configure(
                text=f"⚠️  {clean}" if clean else "⚠️  Unbekannter Fehler",
                text_color="#EF4444",
            )
        else:
            if not self._app.is_configured:
                self._status_label.configure(
                    text=self._app.config_error,
                    text_color="#F59E0B",
                )
            else:
                backend = self._app.settings.transcription_backend
                model   = self._app.settings.local_whisper_model
                mode_text = (
                    f"🔒 Lokal · Whisper {model}"
                    if backend == "local"
                    else "☁️ Online · OpenAI Whisper"
                )
                self._status_label.configure(
                    text=mode_text,
                    text_color=("#22C55E" if backend == "local" else "#6B7280", "#9CA3AF"),
                )

        active_type = wf.workflow_type if wf and phase.is_active else None
        _emojis = {
            WorkflowType.TRANSCRIPTION:  "🎙️",
            WorkflowType.TEXT_IMPROVER:  "✨",
            WorkflowType.DAMPF_ABLASSEN: "🔥",
            WorkflowType.EMOJI_TEXT:     "😊",
            WorkflowType.PROTOKOLL:      "📋",
        }
        for wtype, btn in self._wf_buttons.items():
            label     = self._app.workflow_display_name(wtype)
            emoji     = _emojis[wtype]
            container = self._wf_containers[wtype]
            sub       = self._wf_subtitles[wtype]

            if active_type == wtype:
                # This workflow is running — show Stopp / Processing label
                stop_label = (
                    "■  Stopp"
                    if phase == WorkflowPhase.RECORDING
                    else f"⏳  {wf.state.status_text}"
                )
                btn.configure(text=stop_label, state="normal")
                container.configure(fg_color=wtype.color)
                sub.configure(text="")          # hide subtitle while active
            else:
                disabled = active_type is not None
                btn.configure(
                    text=f"{emoji}  {label}",
                    state="disabled" if disabled else "normal",
                )
                container.configure(
                    fg_color=_dim(wtype.color) if disabled else wtype.color
                )
                sub.configure(text=self._subtitle(wtype))   # restore subtitle

        if self._import_btn:
            self._import_btn.configure(
                state="disabled" if active_type is not None else "normal"
            )

    # ------------------------------------------------------------------
    # Positionierung beim ersten Öffnen
    # ------------------------------------------------------------------

    def _do_show(self) -> None:
        # Nur beim ersten Mal unten rechts positionieren;
        # danach bleibt die vom Nutzer gezogene Position erhalten.
        if self._root.winfo_x() == 0 and self._root.winfo_y() == 0:
            screen_w = self._root.winfo_screenwidth()
            screen_h = self._root.winfo_screenheight()
            x = screen_w - _WINDOW_W - 20
            y = screen_h - _WINDOW_H - 60
            self._root.geometry(f"{_WINDOW_W}x{_WINDOW_H}+{x}+{y}")
        self._update_ui()
        self._root.deiconify()
        self._root.lift()
        self._root.focus_force()
