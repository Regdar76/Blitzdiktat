# Copyright (c) 2026 Thorben Meier. MIT License.
from services import llm_service
from .base_workflow import WorkflowType
from .recording_workflow import RecordingWorkflow


class TextImprovementWorkflow(RecordingWorkflow):
    """Blitzdiktat+: Diktat → sprachlich verbesserter Text."""

    PROCESS_STATUS = "Wird verbessert ..."

    def __init__(
        self,
        settings,
        language: str = "de",
        backend: str = "online",
        local_model: str = "small",
        device: int | None = None,
    ):
        super().__init__(
            WorkflowType.TEXT_IMPROVER,
            settings=settings,
            language=language,
            backend=backend,
            local_model=local_model,
            device=device,
        )

    def _process(self, raw: str) -> str:
        return self._run_async(llm_service.improve(raw, self._settings))
