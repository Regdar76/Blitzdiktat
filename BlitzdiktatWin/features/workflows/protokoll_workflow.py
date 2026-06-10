import asyncio
import threading

from services.audio_recorder import AudioRecorder
from services.transcription_service import transcribe_sync
from services import llm_service
from services.error_handler import friendly_message
from .base_workflow import BaseWorkflow, WorkflowPhase, WorkflowType

MIN_DURATION = 0.4

PROTOKOLL_SYSTEM_PROMPT = (
    "Du bist ein präziser Protokollassistent für Besprechungen, Meetings und Baubesprechungen.\n\n"
    "Du erhältst eine gesprochene, unstrukturierte Aufnahme auf Deutsch oder einer anderen "
    "Sprache. Erstelle daraus ein kompaktes, strukturiertes Besprechungsprotokoll.\n\n"
    "Regeln:\n"
    "- Antworte IMMER auf Deutsch, unabhängig von der Sprache der Eingabe.\n"
    "- Gib NUR das fertige Protokoll zurück — keine Erklärungen, keine Kommentare.\n"
    "- Kein bürokratischer Amtsstil. Sachlich, klar, auf den Punkt.\n"
    "- Teilnehmer: Wenn Namen genannt werden, liste sie auf. Sind Sprecher nicht "
    'identifizierbar, nummeriere sie als "Sprecher 1", "Sprecher 2" usw.\n'
    '- Datum und Thema: Extrahiere aus dem Inhalt wenn moeglich. Wenn nicht genannt -> "-".\n'
    "- Aufgaben: Verantwortliche und Deadlines nur wenn aus dem Inhalt ermittelbar, "
    'sonst "-".\n'
    "- Wenn es keine Entscheidungen oder keine Aufgaben gibt, lasse den jeweiligen "
    "Abschnitt weg.\n\n"
    "## Protokoll\n\n"
    "**Datum:** [Datum oder –]\n"
    "**Thema:** [Thema der Besprechung]\n"
    "**Teilnehmer:** [Namen oder Sprecher 1, Sprecher 2 …]\n\n"
    "---\n\n"
    "### Besprochene Punkte\n"
    "- [Punkt 1]\n"
    "- [Punkt 2]\n\n"
    "### Entscheidungen\n"
    "- [Entscheidung 1 — kurz und präzise]\n\n"
    "### Offene Aufgaben\n"
    "| Aufgabe | Verantwortlich | Deadline |\n"
    "|---------|----------------|----------|\n"
    "| …       | …              | …        |"
)


class ProtokolllWorkflow(BaseWorkflow):
    def __init__(
        self,
        settings,
        language: str = "de",
        backend: str = "online",
        local_model: str = "small",
        device: int | None = None,
    ):
        super().__init__(WorkflowType.PROTOKOLL)
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
            status = (
                f"Wird lokal transkribiert ({self._local_model}) ..."
                if self._backend == "local"
                else "Wird transkribiert ..."
            )
            self._set_phase(WorkflowPhase.PROCESSING, status)
            raw, hint = transcribe_sync(
                path, self._language, [],
                self._backend, self._local_model,
            )

            self._set_phase(WorkflowPhase.PROCESSING, "Protokoll wird erstellt ...")
            system_prompt = (
                getattr(self._settings, "system_prompt", "") or PROTOKOLL_SYSTEM_PROMPT
            )
            loop = asyncio.new_event_loop()
            protokoll = loop.run_until_complete(
                llm_service.protokoll(raw, system_prompt)
            )
            loop.close()

            done_status = f"Fertig. ({hint})" if hint else "Fertig."
            self._set_phase(WorkflowPhase.DONE, status=done_status)
            if self.on_output:
                self.on_output(protokoll)
        except Exception as e:
            self._set_phase(WorkflowPhase.ERROR, error=friendly_message(e))
            self._recorder.discard_recording()
