import asyncio
import threading

from services.audio_recorder import AudioRecorder
from services.transcription_service import transcribe_sync
from services import llm_service
from services.error_handler import friendly_message
from .base_workflow import BaseWorkflow, WorkflowPhase, WorkflowType

MIN_DURATION = 0.4

DEFAULT_SYSTEM_PROMPT = (
    "Du erhältst ein emotional gesprochenes Transkript. Erkenne zuerst das eigentliche Ziel, "
    "Anliegen und den wahren Frust der Person. Formuliere daraus eine klare, respektvolle und "
    "wirksame Nachricht, mit der die Person ihr Ziel eher erreicht. Bewahre relevante Fakten, "
    "konkrete Probleme, Grenzen, Erwartungen und die nötige Dringlichkeit. Entferne Beleidigungen, "
    "Drohungen, Sarkasmus, Unterstellungen und unnötige Eskalation. Wenn mehrere Vorwürfe genannt "
    "werden, verdichte sie auf die entscheidenden Kernpunkte. Der Ton soll ruhig, menschlich, "
    "bestimmt und lösungsorientiert sein. Gib NUR die fertige Nachricht zurück."
)


class DampfAblassenWorkflow(BaseWorkflow):
    def __init__(
        self,
        settings,
        language: str = "de",
        backend: str = "online",
        local_model: str = "small",
        device: int | None = None,
    ):
        super().__init__(WorkflowType.DAMPF_ABLASSEN)
        self._settings = settings
        self._language = language
        self._backend = backend
        self._local_model = local_model
        self._recorder = AudioRecorder(device=device)

    def start(self) -> None:
        self._set_phase(WorkflowPhase.RECORDING, "Aufnahme läuft ...")
        self._recorder.start_recording()
        if self._recorder.error_message:
            self._set_phase(WorkflowPhase.ERROR, error=self._recorder.error_message)

    def stop(self) -> None:
        if not self._recorder.is_recording:
            return
        self._recorder.stop_recording()

        if self._recorder.last_duration < MIN_DURATION:
            self._recorder.discard_recording()
            self._set_phase(WorkflowPhase.ERROR, error="Keine Aufnahme erkannt.")
            return

        self._set_phase(WorkflowPhase.PROCESSING, "Wird vorbereitet ...")
        threading.Thread(target=self._run, daemon=True).start()

    def reset(self) -> None:
        if self._recorder.is_recording:
            self._recorder.stop_recording()
        self._recorder.discard_recording()
        self._set_phase(WorkflowPhase.IDLE)

    @property
    def audio_level(self) -> float:
        return self._recorder.audio_level

    def _run(self) -> None:
        path = self._recorder.recording_path
        if not path:
            self._set_phase(WorkflowPhase.ERROR, error="Keine Aufnahmedatei vorhanden.")
            return
        try:
            custom_terms = getattr(self._settings, "custom_terms", [])
            status = (
                f"Wird lokal transkribiert ({self._local_model}) ..."
                if self._backend == "local"
                else "Wird transkribiert ..."
            )
            self._set_phase(WorkflowPhase.PROCESSING, status)
            raw, hint = transcribe_sync(
                path, self._language, custom_terms,
                self._backend, self._local_model,
            )

            self._set_phase(WorkflowPhase.PROCESSING, "Wird beruhigt ...")
            system_prompt = getattr(self._settings, "system_prompt", "") or DEFAULT_SYSTEM_PROMPT
            loop = asyncio.new_event_loop()
            calmed = loop.run_until_complete(llm_service.dampf_ablassen(raw, system_prompt))
            loop.close()

            done_status = f"Fertig. ({hint})" if hint else "Fertig."
            self._set_phase(WorkflowPhase.DONE, status=done_status)
            if self.on_output:
                self.on_output(calmed)
        except Exception as e:
            self._set_phase(WorkflowPhase.ERROR, error=friendly_message(e))
            self._recorder.discard_recording()   # nur bei Fehler löschen
