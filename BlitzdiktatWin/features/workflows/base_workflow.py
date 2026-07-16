# Copyright (c) 2026 Thorben Meier. MIT License.
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Callable


class WorkflowPhase(Enum):
    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"

    @property
    def is_active(self) -> bool:
        return self in (WorkflowPhase.RECORDING, WorkflowPhase.PROCESSING)


class WorkflowType(Enum):
    TRANSCRIPTION = "transcription"
    TEXT_IMPROVER = "textImprover"
    DAMPF_ABLASSEN = "dampfAblassen"
    EMOJI_TEXT = "emojiText"
    PROTOKOLL = "protokoll"

    @property
    def display_name(self) -> str:
        return {
            "transcription": "Blitzdiktat",
            "textImprover": "Blitzdiktat+",
            "dampfAblassen": "Blitzdiktat $%&!",
            "emojiText": "Blitzdiktat :)",
            "protokoll": "Blitzdiktat Protokoll",
        }[self.value]

    @property
    def subtitle(self) -> str:
        return {
            "transcription": "Sprache rein. Text raus.",
            "textImprover": "Geschrieben sprechen.",
            "dampfAblassen": "Frust rein. Entspannt raus.",
            "emojiText": "Text rein. Emojis dazu.",
            "protokoll": "Besprechung rein. Protokoll raus.",
        }[self.value]

    @property
    def color(self) -> str:
        return {
            "transcription": "#3B82F6",
            "textImprover": "#8B5CF6",
            "dampfAblassen": "#F97316",
            "emojiText": "#06B6D4",
            "protokoll": "#059669",
        }[self.value]

    @property
    def emoji(self) -> str:
        return {
            "transcription": "🎙️",
            "textImprover": "✨",
            "dampfAblassen": "🔥",
            "emojiText": "😊",
            "protokoll": "📋",
        }[self.value]


@dataclass
class WorkflowState:
    phase: WorkflowPhase = WorkflowPhase.IDLE
    status_text: str = ""
    error_text: str = ""


StateCallback = Callable[[WorkflowState], None]
OutputCallback = Callable[[str], None]


class BaseWorkflow(ABC):
    def __init__(self, workflow_type: WorkflowType):
        self.workflow_type = workflow_type
        self.state = WorkflowState()
        self.on_state_change: StateCallback | None = None
        self.on_output: OutputCallback | None = None
        # Nach cancel() darf ein noch laufender Verarbeitungs-Thread weder
        # Phasen melden noch Output liefern — sonst fügt ein alter Workflow
        # seinen Text verspätet ein, nachdem längst ein neuer aktiv ist.
        self.cancelled = False

    def cancel(self) -> None:
        self.cancelled = True
        self.on_state_change = None
        self.on_output = None

    def _set_phase(
        self,
        phase: WorkflowPhase,
        status: str = "",
        error: str = "",
    ) -> None:
        if self.cancelled:
            return
        self.state.phase = phase
        self.state.status_text = status
        self.state.error_text = error
        cb = self.on_state_change
        if cb:
            cb(self.state)

    def _emit_output(self, text: str) -> None:
        cb = self.on_output
        if cb and not self.cancelled:
            cb(text)

    @property
    def is_recording(self) -> bool:
        return self.state.phase == WorkflowPhase.RECORDING

    @abstractmethod
    def start(self) -> None: ...

    @abstractmethod
    def stop(self) -> None: ...

    @abstractmethod
    def reset(self) -> None: ...
