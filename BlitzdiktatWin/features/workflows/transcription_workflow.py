# Copyright (c) 2026 Thorben Meier. MIT License.
import threading

from services.audio_recorder import AudioRecorder
from services.transcription_service import transcribe_sync, apply_voice_commands
from services.error_handler import friendly_message
from .base_workflow import BaseWorkflow, WorkflowPhase, WorkflowType

MIN_DURATION = 0.4


class TranscriptionWorkflow(BaseWorkflow):
    def __init__(
        self,
        language: str = "de",
        custom_terms: list[str] | None = None,
        backend: str = "online",
        local_model: str = "small",
        device: int | None = None,
    ):
        super().__init__(WorkflowType.TRANSCRIPTION)
        self._language = language
        self._custom_terms = custom_terms or []
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
            status = (
                f"Wird lokal transkribiert ({self._local_model}) ..."
                if self._backend == "local"
                else "Wird transkribiert ..."
            )
            self._set_phase(WorkflowPhase.PROCESSING, status)

            text, hint = transcribe_sync(
                path, self._language, self._custom_terms,
                self._backend, self._local_model,
            )
            text = apply_voice_commands(text)
            done_status = f"Fertig. ({hint})" if hint else "Fertig."
            self._set_phase(WorkflowPhase.DONE, status=done_status)
            self._emit_output(text)
        except Exception as e:
            self._set_phase(WorkflowPhase.ERROR, error=friendly_message(e))
            self._recorder.discard_recording()   # nur bei Fehler löschen
