# Copyright (c) 2026 Thorben Meier. MIT License.
"""Gemeinsamer Ablauf aller Aufnahme-Workflows (Template-Method).

Alle fünf Workflows folgen demselben Muster: aufnehmen → transkribieren →
Text verarbeiten → Ergebnis melden. Vorher war dieser Ablauf fünffach
nahezu identisch kopiert (~70 Zeilen pro Klasse) — Bugfixes mussten
fünffach erfolgen. Subklassen implementieren nur noch `_process()` und
setzen optional `PROCESS_STATUS`.
"""

import asyncio
import threading

from services.audio_recorder import AudioRecorder
from services.transcription_service import transcribe_sync
from services.error_handler import friendly_message
from .base_workflow import BaseWorkflow, WorkflowPhase, WorkflowType

MIN_DURATION = 0.4


class RecordingWorkflow(BaseWorkflow):
    # Statuszeile während _process() läuft; None = kein eigener Schritt
    # (z. B. reines Diktat, wo _process nur Sprachkommandos ersetzt).
    PROCESS_STATUS: str | None = None

    def __init__(
        self,
        workflow_type: WorkflowType,
        settings=None,
        language: str = "de",
        backend: str = "online",
        local_model: str = "small",
        device: int | None = None,
        custom_terms: list[str] | None = None,
    ):
        super().__init__(workflow_type)
        self._settings = settings
        self._language = language
        self._backend = backend
        self._local_model = local_model
        # None → Begriffe aus den Settings ableiten (siehe _transcribe_terms)
        self._custom_terms = custom_terms
        self._recorder = AudioRecorder(device=device)

    # ------------------------------------------------------------------
    # Lifecycle (für alle Workflows identisch)
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Template-Method: Transkription + Verarbeitung
    # ------------------------------------------------------------------

    def _run(self) -> None:
        path = self._recorder.recording_path
        if not path:
            self._set_phase(
                WorkflowPhase.ERROR,
                error=self._recorder.error_message or "Keine Aufnahmedatei vorhanden.",
            )
            return
        try:
            status = (
                f"Wird lokal transkribiert ({self._local_model}) ..."
                if self._backend == "local"
                else "Wird transkribiert ..."
            )
            self._set_phase(WorkflowPhase.PROCESSING, status)
            raw, hint = transcribe_sync(
                path, self._language, self._transcribe_terms(),
                self._backend, self._local_model,
            )

            if self.PROCESS_STATUS:
                self._set_phase(WorkflowPhase.PROCESSING, self.PROCESS_STATUS)
            result = self._process(raw)

            done_status = f"Fertig. ({hint})" if hint else "Fertig."
            self._set_phase(WorkflowPhase.DONE, status=done_status)
            self._emit_output(result)
        except Exception as e:
            self._set_phase(WorkflowPhase.ERROR, error=friendly_message(e))
            self._recorder.discard_recording()   # nur bei Fehler löschen

    def _transcribe_terms(self) -> list[str]:
        if self._custom_terms is not None:
            return self._custom_terms
        return getattr(self._settings, "custom_terms", [])

    def _process(self, raw: str) -> str:
        """Verarbeitet das Transkript; Standard = unverändert durchreichen."""
        return raw

    # ------------------------------------------------------------------
    # Helfer
    # ------------------------------------------------------------------

    @staticmethod
    def _run_async(coro):
        """Führt eine Coroutine im Worker-Thread synchron aus."""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
