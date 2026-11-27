# Copyright (c) 2026 Thorben Meier. MIT License.
"""
Hardware-Test und Modellwahl für die lokale KI – Teil der Einstellungen.

* "Hardware prüfen": liest Arbeitsspeicher, Prozessor und Grafikkarte aus und
  empfiehlt das beste Modell, das darauf noch flott läuft.
* Modellliste: alle Modelle des Katalogs, auch die noch nicht installierten.
  "Verwenden" schaltet um; fehlt das Modell, wird es nach Rückfrage geladen.
* "Tempo messen": lässt jedes installierte Modell ein Beispiel-Diktat
  bearbeiten und wählt nach den echten Zeiten das beste vor.
"""

import threading
from tkinter import messagebox
from typing import Callable

import customtkinter as ctk

from services import hardware_probe, llm_service, local_benchmark, model_catalog
from services.model_catalog import CATALOG, LocalModel, Measurement

_GRAY = ("#6B7280", "#9CA3AF")
_GREEN = ("#16A34A", "#22C55E")
_RED = "#EF4444"
_AMBER = "#F59E0B"


class LocalAiPanel(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        app,
        get_url: Callable[[], str],
        get_key: Callable[[], str],
        on_activate: Callable[[str], None],
        on_models: Callable[[list[str]], None],
    ):
        super().__init__(parent, fg_color="transparent")
        self._app = app
        self._get_url = get_url
        self._get_key = get_key
        self._on_activate = on_activate
        self._on_models = on_models

        self._hw: hardware_probe.Hardware | None = None
        self._ratings: dict[str, model_catalog.Rating] = {}
        self._recommended: LocalModel | None = None
        self._installed: list[str] = []
        self._measured: dict[str, Measurement] = {}
        self._progress_text = ""
        self._busy = False

        active = model_catalog.by_key(app.settings.custom_llm_model)
        self._selected: LocalModel = active or CATALOG[0]
        self._labels: dict[str, LocalModel] = {}
        self._build()
        self._load_installed_quietly()

    def _load_installed_quietly(self) -> None:
        """Fragt beim Öffnen, welche Modelle der Server hat – ohne ihn zu starten."""
        url, key = self._get_url(), self._get_key()
        result: dict = {}

        def work() -> None:
            try:
                result["names"] = llm_service.list_models(url, key, timeout=3)
            except Exception:
                result["names"] = []

        def poll() -> None:
            if not self.winfo_exists():
                return
            if "names" not in result:
                self.after(200, poll)
                return
            if result["names"] and not self._installed:
                self._installed = result["names"]
                self._refresh_choices()

        threading.Thread(target=work, daemon=True).start()
        self.after(200, poll)

    # ------------------------------------------------------------------ UI

    def _build(self) -> None:
        ctk.CTkLabel(
            self, text="Hardware-Test und Modellwahl", font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w", pady=(6, 0))
        ctk.CTkLabel(
            self,
            text="Prüft, was dieser Rechner kann, und empfiehlt das passende Sprachmodell. "
                 "Fehlende Modelle lädt Blitzdiktat auf Wunsch selbst herunter.",
            font=ctk.CTkFont(size=11), text_color=_GRAY, wraplength=440, justify="left",
        ).pack(anchor="w", pady=(0, 4))

        self._hw_btn = ctk.CTkButton(
            self, text="🔍  Hardware prüfen und Modell empfehlen", width=300, command=self._check_hardware,
        )
        self._hw_btn.pack(anchor="w", pady=(0, 4))

        self._hw_label = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=11), text_color=_GRAY, wraplength=440, justify="left",
        )
        self._hw_label.pack(anchor="w")

        ctk.CTkLabel(self, text="Modell zur Auswahl").pack(anchor="w", pady=(6, 0))
        self._choice_var = ctk.StringVar()
        self._choice_menu = ctk.CTkOptionMenu(
            self, values=[""], variable=self._choice_var, width=440, dynamic_resizing=False,
            command=self._on_choice,
        )
        self._choice_menu.pack(anchor="w", pady=(0, 2))
        self._detail = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=11), text_color=_GRAY, wraplength=440, justify="left",
        )
        self._detail.pack(anchor="w", pady=(0, 4))

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(anchor="w", pady=(0, 4))
        self._use_btn = ctk.CTkButton(row, text="Verwenden", width=210, command=self._use_selected)
        self._use_btn.pack(side="left", padx=(0, 8))
        self._speed_btn = ctk.CTkButton(
            row, text="⏱  Tempo messen", width=210, command=self._measure_all,
            fg_color=("#6B7280", "#4B5563"), hover_color=("#4B5563", "#374151"),
        )
        self._speed_btn.pack(side="left")

        self._bar = ctk.CTkProgressBar(self, mode="indeterminate", width=440)
        self._status = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=11), text_color=_GRAY, wraplength=440, justify="left",
        )
        self._status.pack(anchor="w", pady=(2, 0))
        self._refresh_choices()

    # ------------------------------------------------------------ Anzeige

    @staticmethod
    def _gb(value: float) -> str:
        return f"{value:.1f}".replace(".", ",") + " GB"

    def _label_for(self, m: LocalModel) -> str:
        stars = "★" * m.quality + "☆" * (5 - m.quality)
        active = model_catalog.by_key(self._app.settings.custom_llm_model)
        if active and active.key == m.key:
            status = "aktiv"
        elif model_catalog.is_installed(m, self._installed):
            status = "installiert"
        else:
            status = "nicht installiert"
        star = "  ⭐" if self._recommended and self._recommended.key == m.key else ""
        return f"{stars}  {m.title}  ·  {self._gb(m.disk_gb)}  ·  {status}{star}"

    def _detail_text(self, m: LocalModel) -> str:
        lines = [m.note]
        meas = self._measured.get(m.key)
        r = self._ratings.get(m.key)
        if meas and meas.ok:
            lines.append(
                f"Gemessen auf diesem Rechner: Diktat ca. {model_catalog.format_duration(meas.dictation_s)}, "
                f"Protokoll ca. {model_catalog.format_duration(meas.protocol_s)} "
                f"({model_catalog.speed_label(meas.protocol_s)})."
            )
        elif r and not r.fits:
            lines.append(f"⚠️  Zu schwer für diesen Rechner: {r.reason}.")
        elif r:
            where = "Grafikkarte" if r.on_gpu else "Prozessor"
            lines.append(
                f"Geschätzt ({where}): Diktat ca. {model_catalog.format_duration(r.est_dictation_s)}, "
                f"Protokoll ca. {model_catalog.format_duration(r.est_protocol_s)}."
            )
        return "\n".join(lines)

    def _refresh_choices(self) -> None:
        self._labels = {self._label_for(m): m for m in CATALOG}
        self._choice_menu.configure(values=list(self._labels))
        for label, m in self._labels.items():
            if m.key == self._selected.key:
                self._choice_var.set(label)
        self._update_use_button()

    def _on_choice(self, label: str) -> None:
        self._selected = self._labels.get(label, self._selected)
        self._update_use_button()

    def _update_use_button(self) -> None:
        m = self._selected
        if model_catalog.is_installed(m, self._installed):
            text = "Verwenden"
        else:
            text = f"Herunterladen und verwenden ({self._gb(m.disk_gb)})"
        self._use_btn.configure(text=text)
        self._detail.configure(text=self._detail_text(m))

    def _set_status(self, text: str, color=_GRAY) -> None:
        self._status.configure(text=text, text_color=color)

    def _set_busy(self, busy: bool, text: str = "") -> None:
        self._busy = busy
        state = "disabled" if busy else "normal"
        for btn in (self._hw_btn, self._use_btn, self._speed_btn):
            btn.configure(state=state)
        self._choice_menu.configure(state=state)
        if busy:
            self._bar.pack(anchor="w", pady=(2, 0), before=self._status)
            self._bar.start()
            self._progress_text = text
            self._set_status(text)
        else:
            self._bar.stop()
            self._bar.pack_forget()

    # ------------------------------------------------------ Hintergrundarbeit

    def _run_bg(self, work: Callable[[], object], done: Callable[[dict], None]) -> None:
        result: dict = {}

        def target() -> None:
            try:
                result["value"] = work()
            except Exception as e:  # Anzeige übernimmt der Hauptthread
                result["error"] = e

        def poll() -> None:
            if not self.winfo_exists():
                return
            if not result:
                self._set_status(self._progress_text)
                self.after(200, poll)
                return
            done(result)

        threading.Thread(target=target, daemon=True).start()
        self.after(200, poll)

    def _progress(self, text: str) -> None:
        self._progress_text = text

    def _refresh_installed(self) -> str:
        """Fragt den Server nach den installierten Modellen. Rückgabe: Fehlertext (leer = ok)."""
        url, key = self._get_url(), self._get_key()
        try:
            self._installed = llm_service.list_models(url, key, timeout=10)
            return ""
        except Exception:
            from services import local_server
            result = local_server.start_local_server(url, force=True)
            if not result.ok:
                return result.reason or "Der lokale Server ist nicht erreichbar."
            try:
                self._installed = llm_service.list_models(url, key, timeout=10)
                return ""
            except Exception as e:
                return str(e)[:150]

    # ------------------------------------------------------------ Hardware

    def _check_hardware(self) -> None:
        self._set_busy(True, "Prüfe Hardware und frage LM Studio … (startet es bei Bedarf)")

        def work() -> dict:
            hw = hardware_probe.detect()
            recommended, ratings = model_catalog.recommend(hw)
            return {"hw": hw, "recommended": recommended, "ratings": ratings, "error": self._refresh_installed()}

        self._run_bg(work, self._hardware_done)

    def _hardware_done(self, result: dict) -> None:
        self._set_busy(False)
        if "error" in result:
            self._set_status(f"❌  Hardware-Prüfung fehlgeschlagen: {str(result['error'])[:150]}", _RED)
            return
        data = result["value"]
        self._hw = data["hw"]
        self._recommended = data["recommended"]
        self._ratings = {r.model.key: r for r in data["ratings"]}
        if self._installed:
            self._on_models(self._installed)

        lines = [f"Dieser Rechner: {self._hw.describe()}"]
        rec = self._recommended
        if rec is None:
            lines.append("⚠️  Für eine lokale KI ist dieser Rechner zu schwach. Besser „Online – OpenAI“ nutzen.")
        else:
            r = self._ratings[rec.key]
            where = "auf der Grafikkarte" if r.on_gpu else "auf dem Prozessor"
            lines.append(
                f"⭐  Empfehlung: {rec.title} – läuft {where}; geschätzt "
                f"Diktat {model_catalog.format_duration(r.est_dictation_s)}, "
                f"Protokoll {model_catalog.format_duration(r.est_protocol_s)}."
            )
            self._selected = rec
        lines.append("Das sind Schätzwerte – „Tempo messen“ ermittelt die echten Zeiten.")
        self._hw_label.configure(text="\n".join(lines))
        self._refresh_choices()
        if data["error"]:
            self._set_status(f"⚠️  Installierte Modelle unbekannt: {data['error']}", _AMBER)
        else:
            self._set_status(f"✅  {len(self._installed)} Modell(e) im Server gefunden.", _GREEN)

    # ------------------------------------------------------------ Verwenden

    def _use_selected(self) -> None:
        m = self._selected
        if model_catalog.is_installed(m, self._installed):
            self._activate(m)
            return
        if not messagebox.askyesno(
            "Modell herunterladen",
            f"{m.title} ist noch nicht installiert.\n\nDownload: ca. {self._gb(m.disk_gb)} von LM Studio "
            f"(Hugging Face). Das kann einige Minuten dauern. Jetzt herunterladen?",
            parent=self.winfo_toplevel(),
        ):
            return
        self._set_busy(True, f"Lade {m.title} herunter ({self._gb(m.disk_gb)}) …")

        def work() -> tuple[bool, str]:
            ok, msg = local_benchmark.download(m, self._get_url(), self._progress)
            if ok:
                self._refresh_installed()
            return ok, msg

        self._run_bg(work, lambda res: self._download_done(m, res))

    def _download_done(self, m: LocalModel, result: dict) -> None:
        self._set_busy(False)
        ok, msg = result["value"] if "value" in result else (False, str(result.get("error", ""))[:150])
        if self._installed:
            self._on_models(self._installed)
        if not ok:
            self._set_status(f"❌  {msg}", _RED)
            self._refresh_choices()
            return
        self._activate(m)

    def _activate(self, m: LocalModel) -> None:
        server_id = model_catalog.server_name(m, self._installed) or m.key
        self._on_activate(server_id)
        self._refresh_choices()
        self._set_status(f"✅  {m.title} wird jetzt für die Textverarbeitung verwendet.", _GREEN)

    # --------------------------------------------------------------- Messen

    def _measure_all(self) -> None:
        self._set_busy(True, "Bereite den Test vor …")

        def work() -> list[Measurement]:
            err = self._refresh_installed()
            if err:
                raise RuntimeError(err)
            todo = [m for m in CATALOG if model_catalog.is_installed(m, self._installed)]
            if not todo:
                raise RuntimeError("Noch kein Modell aus der Liste installiert – erst eines herunterladen.")
            url, key = self._get_url(), self._get_key()
            return [local_benchmark.measure(m, url, key, self._progress) for m in todo]

        self._run_bg(work, self._measure_done)

    def _measure_done(self, result: dict) -> None:
        self._set_busy(False)
        if "error" in result:
            self._set_status(f"❌  {str(result['error'])[:200]}", _RED)
            return
        results: list[Measurement] = result["value"]
        for r in results:
            if r.ok:
                self._measured[r.model.key] = r
        if self._installed:
            self._on_models(self._installed)
        lines = []
        for r in results:
            if r.ok:
                lines.append(
                    f"{r.model.title}: {r.tps:.1f} Tokens/s · Diktat ca. "
                    f"{model_catalog.format_duration(r.dictation_s)} · Protokoll ca. "
                    f"{model_catalog.format_duration(r.protocol_s)} ({model_catalog.speed_label(r.protocol_s)})"
                )
            else:
                lines.append(f"{r.model.title}: ❌ {r.error}")
        best = model_catalog.pick_best(results)
        if best:
            self._recommended = best
            self._selected = best
            lines.append(f"⭐  Beste Wahl für diesen Rechner: {best.title}. Mit „Verwenden“ übernehmen.")
        self._refresh_choices()
        self._set_status("\n".join(lines), _GREEN if best else _AMBER)
