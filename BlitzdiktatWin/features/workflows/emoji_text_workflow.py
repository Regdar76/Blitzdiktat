# Copyright (c) 2026 Thorben Meier. MIT License.
from services import llm_service
from .base_workflow import WorkflowType
from .recording_workflow import RecordingWorkflow


class EmojiTextWorkflow(RecordingWorkflow):
    """Blitzdiktat :): Diktat → Text mit passenden Emojis."""

    PROCESS_STATUS = "Emojis werden hinzugefügt ..."

    def __init__(
        self,
        settings,
        language: str = "de",
        backend: str = "online",
        local_model: str = "small",
        device: int | None = None,
    ):
        super().__init__(
            WorkflowType.EMOJI_TEXT,
            settings=settings,
            language=language,
            backend=backend,
            local_model=local_model,
            device=device,
        )

    def _process(self, raw: str) -> str:
        density = getattr(self._settings, "emoji_density", "mittel")
        return self._run_async(llm_service.add_emojis(raw, density))
