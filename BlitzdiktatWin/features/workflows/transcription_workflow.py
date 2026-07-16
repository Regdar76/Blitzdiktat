# Copyright (c) 2026 Thorben Meier. MIT License.
from services.transcription_service import apply_voice_commands
from .base_workflow import WorkflowType
from .recording_workflow import RecordingWorkflow


class TranscriptionWorkflow(RecordingWorkflow):
    """Reines Diktat: Sprache → Text, Sprachkommandos werden ersetzt."""

    def __init__(
        self,
        language: str = "de",
        custom_terms: list[str] | None = None,
        backend: str = "online",
        local_model: str = "small",
        device: int | None = None,
    ):
        super().__init__(
            WorkflowType.TRANSCRIPTION,
            language=language,
            backend=backend,
            local_model=local_model,
            device=device,
            custom_terms=custom_terms or [],
        )

    def _process(self, raw: str) -> str:
        return apply_voice_commands(raw)
