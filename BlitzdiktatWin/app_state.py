"""
Central app state — mirrors the role of AppState.swift.
Settings are persisted to %APPDATA%\\Blitzdiktat\\settings.json.
"""

import json
import os
import threading
from dataclasses import dataclass, field, asdict
from typing import Callable, Any

from features.workflows.base_workflow import BaseWorkflow, WorkflowState, WorkflowType
from features.workflows.transcription_workflow import TranscriptionWorkflow
from features.workflows.text_improvement_workflow import TextImprovementWorkflow
from features.workflows.dampf_ablassen_workflow import DampfAblassenWorkflow
from features.workflows.emoji_text_workflow import EmojiTextWorkflow
from features.workflows.protokoll_workflow import ProtokolllWorkflow
from services.hotkey_service import HotkeyService
from services import credentials_service, paste_service
from services.audio_recorder import find_device_index
from services.transcript_store import save_transcript, save_protocol_as_pdf


# ------------------------------------------------------------------
# Settings dataclasses (JSON-serialisierbar)
# ------------------------------------------------------------------

@dataclass
class TextImprovementSettings:
    system_prompt: str = ""
    custom_terms: list[str] = field(default_factory=list)
    context: str = ""
    tone: str = "neutral"        # formal | neutral | casual
    custom_name: str = ""


@dataclass
class DampfAblassenSettings:
    system_prompt: str = ""
    custom_name: str = ""


@dataclass
class EmojiTextSettings:
    emoji_density: str = "mittel"   # wenig | mittel | viel
    custom_name: str = ""


@dataclass
class ProtokolllSettings:
    system_prompt: str = ""
    custom_name: str = ""


@dataclass
class AppSettings:
    language: str = "de"
    has_seen_onboarding: bool = False
    last_seen_version: str = ""
    hotkey_transcription: str = "ctrl+shift+r"
    hotkey_text_improver: str = "ctrl+shift+t"
    hotkey_dampf_ablassen: str = "ctrl+shift+d"
    hotkey_emoji_text: str = "ctrl+shift+e"
    hotkey_protokoll: str = "ctrl+shift+p"
    transcription_backend: str = "local"    # "online" | "local"
    local_whisper_model: str = "small"
    selected_microphone: str = ""           # "" = Systemstandard
    text_improvement: TextImprovementSettings = field(default_factory=TextImprovementSettings)
    dampf_ablassen: DampfAblassenSettings = field(default_factory=DampfAblassenSettings)
    emoji_text: EmojiTextSettings = field(default_factory=EmojiTextSettings)
    protokoll: ProtokolllSettings = field(default_factory=ProtokolllSettings)


# ------------------------------------------------------------------
# Persistence
# ------------------------------------------------------------------

def _settings_path() -> str:
    app_data = os.environ.get("APPDATA", os.path.expanduser("~"))
    folder = os.path.join(app_data, "Blitzdiktat")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "settings.json")


def _load_settings() -> AppSettings:
    path = _settings_path()
    if not os.path.exists(path):
        return AppSettings()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        s = AppSettings()
        s.language = data.get("language", s.language)
        s.has_seen_onboarding = data.get("has_seen_onboarding", s.has_seen_onboarding)
        s.last_seen_version = data.get("last_seen_version", s.last_seen_version)
        s.hotkey_transcription = data.get("hotkey_transcription", s.hotkey_transcription)
        s.hotkey_text_improver = data.get("hotkey_text_improver", s.hotkey_text_improver)
        s.hotkey_dampf_ablassen = data.get("hotkey_dampf_ablassen", s.hotkey_dampf_ablassen)
        s.hotkey_emoji_text = data.get("hotkey_emoji_text", s.hotkey_emoji_text)
        s.hotkey_protokoll = data.get("hotkey_protokoll", s.hotkey_protokoll)
        s.transcription_backend = data.get("transcription_backend", s.transcription_backend)
        s.local_whisper_model = data.get("local_whisper_model", s.local_whisper_model)
        s.selected_microphone = data.get("selected_microphone", s.selected_microphone)

        ti = data.get("text_improvement", {})
        s.text_improvement = TextImprovementSettings(
            system_prompt=ti.get("system_prompt", ""),
            custom_terms=ti.get("custom_terms", []),
            context=ti.get("context", ""),
            tone=ti.get("tone", "neutral"),
            custom_name=ti.get("custom_name", ""),
        )

        da = data.get("dampf_ablassen", {})
        s.dampf_ablassen = DampfAblassenSettings(
            system_prompt=da.get("system_prompt", ""),
            custom_name=da.get("custom_name", ""),
        )

        et = data.get("emoji_text", {})
        s.emoji_text = EmojiTextSettings(
            emoji_density=et.get("emoji_density", "mittel"),
            custom_name=et.get("custom_name", ""),
        )

        pr = data.get("protokoll", {})
        s.protokoll = ProtokolllSettings(
            system_prompt=pr.get("system_prompt", ""),
            custom_name=pr.get("custom_name", ""),
        )
        return s
    except Exception:
        return AppSettings()


def _save_settings(s: AppSettings) -> None:
    data = {
        "language": s.language,
        "has_seen_onboarding": s.has_seen_onboarding,
        "last_seen_version": s.last_seen_version,
        "hotkey_transcription": s.hotkey_transcription,
        "hotkey_text_improver": s.hotkey_text_improver,
        "hotkey_dampf_ablassen": s.hotkey_dampf_ablassen,
        "hotkey_emoji_text": s.hotkey_emoji_text,
        "transcription_backend": s.transcription_backend,
        "local_whisper_model": s.local_whisper_model,
        "selected_microphone": s.selected_microphone,
        "text_improvement": asdict(s.text_improvement),
        "dampf_ablassen": asdict(s.dampf_ablassen),
        "emoji_text": asdict(s.emoji_text),
        "protokoll": asdict(s.protokoll),
    }
    try:
        with open(_settings_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ------------------------------------------------------------------
# AppState
# ------------------------------------------------------------------

AppStateCallback = Callable[["AppState"], None]


class AppState:
    def __init__(self):
        self.settings: AppSettings = _load_settings()
        self.active_workflow: BaseWorkflow | None = None
        self.hotkey_service = HotkeyService()
        self._subscribers: list[AppStateCallback] = []
        self._target_hwnd: int = 0
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Subscription
    # ------------------------------------------------------------------

    def subscribe(self, callback: AppStateCallback) -> None:
        self._subscribers.append(callback)

    def _notify(self) -> None:
        for cb in self._subscribers:
            try:
                cb(self)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Computed
    # ------------------------------------------------------------------

    @property
    def is_configured(self) -> bool:
        if self.settings.transcription_backend == "local":
            from services.local_transcription_service import AVAILABLE
            return AVAILABLE
        return credentials_service.is_configured()

    @property
    def config_error(self) -> str:
        """Liefert eine lesbare Fehlermeldung wenn is_configured False ist."""
        if self.settings.transcription_backend == "local":
            from services.local_transcription_service import _IMPORT_ERROR
            return (
                f"faster-whisper nicht verfügbar: {_IMPORT_ERROR}. "
                "Bitte 'pip install faster-whisper' ausführen."
                if _IMPORT_ERROR
                else "faster-whisper nicht installiert. Bitte 'pip install faster-whisper' ausführen."
            )
        return "API Key fehlt — Einstellungen öffnen"

    def workflow_display_name(self, wtype: WorkflowType) -> str:
        name_map = {
            WorkflowType.TEXT_IMPROVER: self.settings.text_improvement.custom_name,
            WorkflowType.DAMPF_ABLASSEN: self.settings.dampf_ablassen.custom_name,
            WorkflowType.EMOJI_TEXT: self.settings.emoji_text.custom_name,
            WorkflowType.PROTOKOLL: self.settings.protokoll.custom_name,
        }
        custom = name_map.get(wtype, "").strip()
        return custom if custom else wtype.display_name

    # ------------------------------------------------------------------
    # Workflow management
    # ------------------------------------------------------------------

    def capture_target_window(self) -> None:
        hwnd = paste_service.get_foreground_hwnd()
        with self._lock:
            self._target_hwnd = hwnd

    def start_workflow(self, wtype: WorkflowType) -> None:
        if not self.is_configured:
            return

        self._stop_active()

        workflow: BaseWorkflow
        s = self.settings

        backend = s.transcription_backend
        local_model = s.local_whisper_model
        device = find_device_index(s.selected_microphone)

        if wtype == WorkflowType.TRANSCRIPTION:
            workflow = TranscriptionWorkflow(
                language=s.language,
                custom_terms=s.text_improvement.custom_terms,
                backend=backend, local_model=local_model, device=device,
            )
        elif wtype == WorkflowType.TEXT_IMPROVER:
            workflow = TextImprovementWorkflow(
                settings=s.text_improvement, language=s.language,
                backend=backend, local_model=local_model, device=device,
            )
        elif wtype == WorkflowType.DAMPF_ABLASSEN:
            workflow = DampfAblassenWorkflow(
                settings=s.dampf_ablassen, language=s.language,
                backend=backend, local_model=local_model, device=device,
            )
        elif wtype == WorkflowType.EMOJI_TEXT:
            workflow = EmojiTextWorkflow(
                settings=s.emoji_text, language=s.language,
                backend=backend, local_model=local_model, device=device,
            )
        elif wtype == WorkflowType.PROTOKOLL:
            workflow = ProtokolllWorkflow(
                settings=s.protokoll, language=s.language,
                backend=backend, local_model=local_model, device=device,
            )
        else:
            return

        workflow.on_state_change = self._on_workflow_state
        workflow.on_output = self._on_workflow_output

        with self._lock:
            self.active_workflow = workflow

        workflow.start()
        self._notify()

    def stop_workflow(self) -> None:
        with self._lock:
            wf = self.active_workflow
        if wf:
            wf.stop()

    def reset_workflow(self) -> None:
        self._stop_active()
        with self._lock:
            self.active_workflow = None
        self._notify()

    def save_settings(self) -> None:
        _save_settings(self.settings)
        self._rebind_hotkeys()

    # ------------------------------------------------------------------
    # Hotkey wiring
    # ------------------------------------------------------------------

    def bind_hotkeys(self) -> None:
        self._rebind_hotkeys()
        self.hotkey_service.start()

    def _rebind_hotkeys(self) -> None:
        self.hotkey_service.unregister_all()
        s = self.settings

        def _bind(combo: str, wtype: WorkflowType) -> None:
            if not combo:
                return
            self.hotkey_service.register(
                combo,
                on_press=lambda: self._hotkey_press(wtype),
                on_release=lambda: self._hotkey_release(wtype),
            )

        _bind(s.hotkey_transcription, WorkflowType.TRANSCRIPTION)
        _bind(s.hotkey_text_improver, WorkflowType.TEXT_IMPROVER)
        _bind(s.hotkey_dampf_ablassen, WorkflowType.DAMPF_ABLASSEN)
        _bind(s.hotkey_emoji_text, WorkflowType.EMOJI_TEXT)
        _bind(s.hotkey_protokoll, WorkflowType.PROTOKOLL)

    def _hotkey_press(self, wtype: WorkflowType) -> None:
        self.capture_target_window()
        self.start_workflow(wtype)

    def _hotkey_release(self, wtype: WorkflowType) -> None:
        with self._lock:
            wf = self.active_workflow
        if wf and wf.workflow_type == wtype and wf.is_recording:
            wf.stop()

    # ------------------------------------------------------------------
    # Workflow callbacks
    # ------------------------------------------------------------------

    def _on_workflow_state(self, state: WorkflowState) -> None:
        self._notify()

    def _on_workflow_output(self, text: str) -> None:
        with self._lock:
            hwnd = self._target_hwnd
            wf = self.active_workflow
        workflow_name = wf.workflow_type.display_name if wf else ""
        wf_type = wf.workflow_type if wf else None

        threading.Thread(
            target=paste_service.paste_to_window,
            args=(hwnd, text),
            daemon=True,
        ).start()
        threading.Thread(
            target=save_transcript,
            args=(text, workflow_name),
            daemon=True,
        ).start()
        if wf_type == WorkflowType.PROTOKOLL:
            threading.Thread(
                target=save_protocol_as_pdf,
                args=(text,),
                daemon=True,
            ).start()
        self._notify()

    def _stop_active(self) -> None:
        with self._lock:
            wf = self.active_workflow
        if wf:
            wf.reset()
