# Copyright (c) 2026 Thorben Meier. MIT License.
from services import llm_service
from .base_workflow import WorkflowType
from .recording_workflow import RecordingWorkflow

# Rückwärtskompatibler Name; die Prompts liegen gesammelt in services/prompts.py.
from services.prompts import DAMPF_SYSTEM_PROMPT as DEFAULT_SYSTEM_PROMPT  # noqa: F401


class DampfAblassenWorkflow(RecordingWorkflow):
    """Blitzdiktat $%&!: Frust rein → ruhige, sachliche Nachricht raus."""

    PROCESS_STATUS = "Wird beruhigt ..."

    def __init__(
        self,
        settings,
        language: str = "de",
        backend: str = "online",
        local_model: str = "small",
        device: int | None = None,
    ):
        super().__init__(
            WorkflowType.DAMPF_ABLASSEN,
            settings=settings,
            language=language,
            backend=backend,
            local_model=local_model,
            device=device,
        )

    def _process(self, raw: str) -> str:
        # Leer = eingebauter Prompt; welcher (OpenAI oder lokales Modell),
        # entscheidet llm_service anhand des gewählten KI-Anbieters.
        custom_prompt = getattr(self._settings, "system_prompt", "") or ""
        return self._run_async(llm_service.dampf_ablassen(raw, custom_prompt))
