# Copyright (c) 2026 Thorben Meier. MIT License.
from services import llm_service
from .base_workflow import WorkflowType
from .recording_workflow import RecordingWorkflow

DEFAULT_SYSTEM_PROMPT = (
    "Du erhältst ein emotional gesprochenes Transkript. Erkenne zuerst das eigentliche Ziel, "
    "Anliegen und den wahren Frust der Person. Formuliere daraus eine klare, respektvolle und "
    "wirksame Nachricht, mit der die Person ihr Ziel eher erreicht. Bewahre relevante Fakten, "
    "konkrete Probleme, Grenzen, Erwartungen und die nötige Dringlichkeit. Entferne Beleidigungen, "
    "Drohungen, Sarkasmus, Unterstellungen und unnötige Eskalation. Wenn mehrere Vorwürfe genannt "
    "werden, verdichte sie auf die entscheidenden Kernpunkte. Der Ton soll ruhig, menschlich, "
    "bestimmt und lösungsorientiert sein. Gib NUR die fertige Nachricht zurück."
)


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
        system_prompt = getattr(self._settings, "system_prompt", "") or DEFAULT_SYSTEM_PROMPT
        return self._run_async(llm_service.dampf_ablassen(raw, system_prompt))
