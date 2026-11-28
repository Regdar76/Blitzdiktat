# Copyright (c) 2026 Thorben Meier. MIT License.
"""
Blitzdiktat Notiz – kleines Fenster zum Diktieren, Einfügen, Überarbeiten und Kopieren.

* Diktierter Text erscheint hier statt im Zielfenster; weiter diktieren hängt an.
* Beliebiger Text lässt sich einfügen (Strg+V oder "Einfügen") und dann mit
  "Verbessern", "Beruhigen" oder "Emojis" überarbeiten. Ist etwas markiert,
  wirkt der Knopf nur auf die Markierung, sonst auf den ganzen Text.
* "Zurück" nimmt die letzte Änderung zurück.
* "Kopieren" legt den Text in die Zwischenablage, "Exportieren" speichert ihn
  als Textdatei oder PDF. Der Entwurf bleibt bis zum nächsten Öffnen erhalten.
"""

import threading
import tkinter as tk
from tkinter import filedialog

import customtkinter as ctk

from app_state import AppState
from features.workflows.base_workflow import WorkflowPhase, WorkflowType
from services import llm_service, note_service, paste_service
from services.error_handler import friendly_message

_W, _H = 480, 470
_SAVE_DELAY_MS = 700
_HISTORY_MAX = 20
_GRAY = ("#6B7280", "#9CA3AF")
_GREEN = ("#16A34A", "#22C55E")
_RED = "#EF4444"
_AMBER = "#F59E0B"

# Überarbeitungen: Knopf → (Beschriftung, Statustext)
TRANSFORMS = {
    "improve": ("✨  Verbessern", "Wird verbessert …"),
    "calm": ("🔥  Beruhigen", "Wird beruhigt …"),
    "emoji": ("😊  Emojis", "Emojis werden ergänzt …"),
}


class NotizWindow(ctk.CTkToplevel):
    def __init__(self, parent, app_state: AppState):
        super().__init__(parent)
        self._app = app_state
        self._history: list[str] = []
        self._save_job = None
        self._status_job = None
        self._busy = False
        self._placed = False

        self.title("Blitzdiktat – Notiz")
        self.geometry(f"{_W}x{_H}")
        self.minsize(380, 360)
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self.hide)
        self.update_idletasks()
        paste_service.register_own_window(self.winfo_id())
        self._build()
        self._text.insert("1.0", note_service.load_draft())
        self.refresh()

    # ------------------------------------------------------------------ Aufbau

    def _build(self) -> None:
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=12, pady=(10, 4))
        ctk.CTkLabel(head, text="📝  Notiz", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        self._pin_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(
            head, text="Im Vordergrund", variable=self._pin_var, width=40,
            font=ctk.CTkFont(size=11), command=self._toggle_pin,
        ).pack(side="right")

        self._text = ctk.CTkTextbox(self, wrap="word", font=ctk.CTkFont(size=13), undo=True)
        self._text.pack(fill="both", expand=True, padx=12, pady=(0, 6))
        self._text.bind("<<Modified>>", self._on_modified)

        self._status = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=11), text_color=_GRAY, anchor="w", justify="left",
            wraplength=_W - 30,
        )
        self._status.pack(fill="x", padx=14)

        row1 = ctk.CTkFrame(self, fg_color="transparent")
        row1.pack(fill="x", padx=12, pady=(4, 0))
        self._dictate_btn = ctk.CTkButton(row1, text="🎙  Diktieren", command=self._toggle_dictation)
        self._dictate_btn.pack(side="left", expand=True, fill="x", padx=(0, 4))
        self._paste_btn = ctk.CTkButton(
            row1, text="📥  Einfügen", command=self._paste_clipboard,
            fg_color=("#6B7280", "#4B5563"), hover_color=("#4B5563", "#374151"),
        )
        self._paste_btn.pack(side="left", expand=True, fill="x")

        row2 = ctk.CTkFrame(self, fg_color="transparent")
        row2.pack(fill="x", padx=12, pady=(4, 0))
        self._transform_btns: dict[str, ctk.CTkButton] = {}
        colors = {"improve": "#8B5CF6", "calm": "#F97316", "emoji": "#06B6D4"}
        for key, (label, _) in TRANSFORMS.items():
            btn = ctk.CTkButton(
                row2, text=label, fg_color=colors[key], command=lambda k=key: self._transform(k),
            )
            btn.pack(side="left", expand=True, fill="x", padx=(0, 4))
            self._transform_btns[key] = btn
        self._undo_btn = ctk.CTkButton(
            row2, text="↶", width=40, command=self._undo,
            fg_color=("#6B7280", "#4B5563"), hover_color=("#4B5563", "#374151"),
        )
        self._undo_btn.pack(side="left")

        row3 = ctk.CTkFrame(self, fg_color="transparent")
        row3.pack(fill="x", padx=12, pady=(4, 12))
        self._new_btn = ctk.CTkButton(
            row3, text="🗑  Neu", width=80, command=self._new_note,
            fg_color="transparent", border_width=1,
            border_color=("#D1D5DB", "#4B5563"), text_color=("#374151", "#D1D5DB"),
        )
        self._new_btn.pack(side="left", padx=(0, 4))
        self._export_btn = ctk.CTkButton(
            row3, text="💾  Exportieren", command=self._show_export_menu,
            fg_color="transparent", border_width=1,
            border_color=("#D1D5DB", "#4B5563"), text_color=("#374151", "#D1D5DB"),
        )
        self._export_btn.pack(side="left", expand=True, fill="x", padx=(0, 4))
        self._copy_btn = ctk.CTkButton(
            row3, text="📋  Kopieren", command=self._copy, font=ctk.CTkFont(weight="bold"),
        )
        self._copy_btn.pack(side="left", expand=True, fill="x")

        self._export_menu = tk.Menu(self, tearoff=0)
        self._export_menu.add_command(label="Als Textdatei (.txt) …", command=lambda: self._export("txt"))
        self._export_menu.add_command(label="Als PDF (.pdf) …", command=lambda: self._export("pdf"))

    # --------------------------------------------------------------- Anzeige

    def show(self) -> None:
        if not self._placed:
            self._placed = True
            x = max(0, self.winfo_screenwidth() - 300 - 20 - _W - 12)
            y = max(0, self.winfo_screenheight() - _H - 60)
            self.geometry(f"{_W}x{_H}+{x}+{y}")
        self.deiconify()
        self.lift()
        self.focus_force()

    def hide(self) -> None:
        self._flush_save()
        self.withdraw()

    def _toggle_pin(self) -> None:
        self.attributes("-topmost", bool(self._pin_var.get()))

    def _say(self, text: str, color=_GRAY, reset_after_ms: int = 0) -> None:
        self._status.configure(text=text, text_color=color)
        if self._status_job:
            self.after_cancel(self._status_job)
            self._status_job = None
        if reset_after_ms:
            self._status_job = self.after(reset_after_ms, lambda: self._status.configure(text=""))

    def refresh(self) -> None:
        """Passt Knöpfe und Hinweis an den Zustand der Aufnahme an (aus dem Hauptthread)."""
        wf = self._app.active_workflow
        note_wf = wf if wf and wf.workflow_type == WorkflowType.NOTIZ else None
        phase = note_wf.state.phase if note_wf else WorkflowPhase.IDLE
        other_active = bool(wf and not note_wf and wf.state.phase.is_active)

        if phase == WorkflowPhase.RECORDING:
            self._dictate_btn.configure(text="■  Stopp", fg_color=_RED, hover_color="#DC2626", state="normal")
            self._say("🔴  Aufnahme läuft … Sprechen, dann Stopp.", _RED)
        elif phase == WorkflowPhase.PROCESSING:
            self._dictate_btn.configure(text=f"⏳  {note_wf.state.status_text}"[:28], state="disabled")
            self._say(f"⏳  {note_wf.state.status_text}", _AMBER)
        else:
            label = "🎙  Weiter diktieren" if self._text.get("1.0", "end").strip() else "🎙  Diktieren"
            self._dictate_btn.configure(
                text=label, fg_color=["#3B8ED0", "#1F6AA5"], hover_color=["#36719F", "#144870"],
                state="disabled" if (other_active or self._busy) else "normal",
            )
            if phase == WorkflowPhase.ERROR and note_wf and note_wf.state.error_text:
                self._say("⚠️  " + note_wf.state.error_text.split("\n")[0][:120], _RED)

    # ---------------------------------------------------------------- Text

    def get_text(self) -> str:
        return self._text.get("1.0", "end-1c")

    def set_text(self, text: str, remember: bool = True) -> None:
        if remember and text != self.get_text():
            self._remember()
        self._text.delete("1.0", "end")
        self._text.insert("1.0", text)
        self._text.edit_modified(False)
        self._schedule_save()
        self.refresh()

    def _selection(self) -> tuple[str, str] | None:
        try:
            return self._text.index("sel.first"), self._text.index("sel.last")
        except tk.TclError:
            return None

    def append_dictation(self, text: str) -> None:
        """Hängt diktierten Text ans Ende an und zeigt das Fenster."""
        self._remember()
        self.set_text(note_service.join_dictation(self.get_text(), text), remember=False)
        self._text.see("end")
        self.show()
        self._say("✅  Text hinzugefügt.", _GREEN, 4000)

    def _remember(self) -> None:
        current = self.get_text()
        if self._history and self._history[-1] == current:
            return
        self._history.append(current)
        del self._history[:-_HISTORY_MAX]

    def _undo(self) -> None:
        if not self._history:
            self._say("Nichts zum Zurücknehmen.", _GRAY, 3000)
            return
        self.set_text(self._history.pop(), remember=False)
        self._say("↶  Letzte Änderung zurückgenommen.", _GRAY, 3000)

    def _new_note(self) -> None:
        if not self.get_text().strip():
            return
        self._remember()
        self.set_text("", remember=False)
        self._say("Neue Notiz. Mit ↶ lässt sich die alte zurückholen.", _GRAY, 5000)

    # ------------------------------------------------------------ Entwurf

    def _on_modified(self, _event=None) -> None:
        if self._text.edit_modified():
            self._text.edit_modified(False)
            self._schedule_save()
            self.refresh()

    def _schedule_save(self) -> None:
        if self._save_job:
            self.after_cancel(self._save_job)
        self._save_job = self.after(_SAVE_DELAY_MS, self._flush_save)

    def _flush_save(self) -> None:
        if self._save_job:
            self.after_cancel(self._save_job)
            self._save_job = None
        note_service.save_draft(self.get_text())

    # --------------------------------------------------------- Diktieren

    def _toggle_dictation(self) -> None:
        busy = getattr(self._app, "setup_busy", lambda: None)()
        if busy:
            self._say(f"⏳  Blitzdiktat richtet sich noch ein – bitte warten. {busy}", _AMBER)
            return
        wf = self._app.active_workflow
        if wf and wf.workflow_type == WorkflowType.NOTIZ and wf.is_recording:
            self._app.stop_workflow()
        else:
            self._app.capture_target_window()
            self._app.start_workflow(WorkflowType.NOTIZ)

    # ------------------------------------------------- Einfügen / Kopieren

    def _clipboard_text(self) -> str:
        try:
            return self.clipboard_get()
        except tk.TclError:
            return ""

    def _paste_clipboard(self) -> None:
        text = self._clipboard_text()
        if not text.strip():
            self._say("Die Zwischenablage enthält keinen Text.", _AMBER, 4000)
            return
        self._remember()
        sel = self._selection()
        if sel:
            self._text.delete(*sel)
            self._text.insert(sel[0], text)
        elif not self.get_text().strip():
            self._text.delete("1.0", "end")
            self._text.insert("1.0", text)
        else:
            self._text.insert("insert", text)
        self._schedule_save()
        self.refresh()
        self._say("📥  Text eingefügt. Jetzt verbessern, beruhigen oder kopieren.", _GREEN, 5000)

    def _copy(self) -> None:
        sel = self._selection()
        text = self._text.get(*sel) if sel else self.get_text()
        if not text.strip():
            self._say("Kein Text zum Kopieren.", _AMBER, 3000)
            return
        paste_service.copy_to_clipboard(text)
        self._say("✅  Auswahl kopiert." if sel else "✅  Text kopiert.", _GREEN, 3000)

    # ------------------------------------------------------------- Export

    def _show_export_menu(self) -> None:
        if not self.get_text().strip():
            self._say("Kein Text zum Exportieren.", _AMBER, 3000)
            return
        x = self._export_btn.winfo_rootx()
        y = self._export_btn.winfo_rooty() + self._export_btn.winfo_height()
        self._export_menu.tk_popup(x, y)

    def _export(self, kind: str) -> None:
        text = self.get_text()
        path = filedialog.asksaveasfilename(
            parent=self, title="Notiz exportieren",
            defaultextension=f".{kind}", initialfile=note_service.suggested_filename(kind),
            filetypes=[("PDF-Dokument", "*.pdf")] if kind == "pdf" else [("Textdatei", "*.txt")],
        )
        if not path:
            return
        try:
            if kind == "pdf":
                if not note_service.export_pdf(path, text):
                    self._say("❌  PDF-Export nicht verfügbar (reportlab fehlt).", _RED)
                    return
            else:
                note_service.export_text(path, text)
        except OSError as e:
            self._say(f"❌  Speichern nicht möglich: {str(e)[:100]}", _RED)
            return
        self._say(f"✅  Gespeichert: {path}", _GREEN, 8000)

    # ------------------------------------------------------- Überarbeiten

    def _transform(self, kind: str) -> None:
        if self._busy:
            return
        problem = llm_service.config_problem()
        if problem:
            self._say(f"⚠️  {problem}", _AMBER)
            return
        sel = self._selection()
        source = self._text.get(*sel) if sel else self.get_text()
        if not source.strip():
            self._say("Erst Text diktieren oder einfügen.", _AMBER, 4000)
            return

        coro_factory = self._coroutine_for(kind, source)
        self._set_busy(True, TRANSFORMS[kind][1])
        result: dict = {}

        def work() -> None:
            import asyncio
            loop = asyncio.new_event_loop()
            try:
                result["text"] = loop.run_until_complete(coro_factory())
            except Exception as e:
                result["error"] = e
            finally:
                loop.close()

        def poll() -> None:
            if not self.winfo_exists():
                return
            if not result:
                self.after(150, poll)
                return
            self._set_busy(False)
            if "error" in result:
                self._say("⚠️  " + friendly_message(result["error"]).split("\n")[0][:140], _RED)
                return
            self._apply_result(result["text"], sel)

        threading.Thread(target=work, daemon=True).start()
        self.after(150, poll)

    def _coroutine_for(self, kind: str, text: str):
        s = self._app.settings
        if kind == "improve":
            return lambda: llm_service.improve(text, s.text_improvement)
        if kind == "calm":
            return lambda: llm_service.dampf_ablassen(text, getattr(s.dampf_ablassen, "system_prompt", "") or "")
        return lambda: llm_service.add_emojis(text, getattr(s.emoji_text, "emoji_density", "mittel"))

    def _apply_result(self, text: str, sel: tuple[str, str] | None) -> None:
        self._remember()
        if sel:
            self._text.delete(*sel)
            self._text.insert(sel[0], text)
        else:
            self._text.delete("1.0", "end")
            self._text.insert("1.0", text)
        self._schedule_save()
        self.refresh()
        self._say("✅  Fertig. Mit ↶ lässt sich die Änderung zurücknehmen.", _GREEN, 6000)

    def _set_busy(self, busy: bool, text: str = "") -> None:
        self._busy = busy
        state = "disabled" if busy else "normal"
        for btn in (*self._transform_btns.values(), self._paste_btn, self._new_btn, self._undo_btn):
            btn.configure(state=state)
        if busy:
            self._say("⏳  " + text, _AMBER)
        self.refresh()
