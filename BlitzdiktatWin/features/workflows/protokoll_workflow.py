# Copyright (c) 2026 Thorben Meier. MIT License.
import asyncio
import os
import threading

from services.audio_recorder import AudioRecorder
from services.transcription_service import transcribe_sync
from services import llm_service
from services.error_handler import friendly_message
from .base_workflow import BaseWorkflow, WorkflowPhase, WorkflowType

MIN_DURATION = 0.4

AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".aac", ".wma"}
TEXT_EXTENSIONS  = {".txt", ".md"}

PROTOKOLL_SYSTEM_PROMPT = (
    "Du bist ein präziser Protokollassistent für Besprechungen, Meetings und Baubesprechungen.\n\n"
    "Du erhältst eine gesprochene, unstrukturierte Aufnahme auf Deutsch oder einer anderen "
    "Sprache. Erstelle daraus ein kompaktes, strukturiertes Besprechungsprotokoll.\n\n"
    "Regeln:\n"
    "- Antworte IMMER auf Deutsch, unabhängig von der Sprache der Eingabe.\n"
    "- Gib NUR das fertige Protokoll zurück — keine Erklärungen, keine Kommentare, "
    "keine Codeblöcke.\n"
    "- Erfinde keine Inhalte. Nimm nur auf, was tatsächlich gesagt wurde.\n"
    "- Kein bürokratischer Amtsstil. Sachlich, klar, auf den Punkt.\n"
    "- Teilnehmer: Nur auflisten, wenn Namen im Gespräch genannt werden. Sonst lasse "
    "die Teilnehmer-Zeile weg. Ordne Aussagen niemals erratenen Sprechern zu.\n"
    "- Übernimm Zahlen, Maße, Beträge und Termine exakt wie genannt — runde und "
    "interpretiere nicht.\n"
    "- Datum: Verwende das angegebene Aufnahmedatum, sofern im Gespräch kein anderes "
    'Besprechungsdatum genannt wird. Thema: Extrahiere aus dem Inhalt, sonst "–".\n'
    "- Rechne relative Zeitangaben (morgen, nächste Woche, Ende des Monats) anhand "
    "des Aufnahmedatums in konkrete Daten um.\n"
    "- Aufgaben: Verantwortliche und Deadlines nur wenn aus dem Inhalt ermittelbar, "
    'sonst "–".\n'
    "- Wenn es keine Entscheidungen oder keine Aufgaben gibt, lasse den jeweiligen "
    "Abschnitt weg.\n"
    "- Nächster Termin: Nur angeben, wenn ein konkreter Folgetermin oder ein "
    "nächstes Treffen genannt wird (Datum/Uhrzeit und ggf. Anlass). Wird keiner "
    "genannt, lasse den Abschnitt weg.\n"
    "- Gib keine Platzhalter- oder Beispielzeilen aus.\n"
    "- Gruppiere die besprochenen Punkte bei längeren Besprechungen thematisch "
    "mit Zwischenüberschriften.\n"
    "- Beginne das Protokoll mit einer Zusammenfassung in 4–6 Sätzen, "
    "die so geschrieben ist, dass auch eine Person, die nicht dabei war und den "
    "Rest des Protokolls nicht liest, vollständig versteht, worum es ging: "
    "Ausgangslage bzw. Anlass, das Thema, die wichtigsten besprochenen Inhalte "
    "sowie das zentrale Ergebnis und die nächsten Schritte. Die Zusammenfassung "
    "muss für sich allein verständlich sein — keine ungeklärten Abkürzungen, "
    "Namen ohne Rolle oder Insider-Bezüge.\n\n"
    "## Protokoll\n\n"
    "**Datum:** [Datum oder –]\n"
    "**Thema:** [Thema der Besprechung]\n"
    "**Teilnehmer:** [Namen, nur falls genannt — sonst Zeile weglassen]\n\n"
    "---\n\n"
    "### Zusammenfassung\n"
    "[4–6 Sätze, die auch einer außenstehenden Person vollständig klarmachen, worum "
    "es ging: Ausgangslage/Anlass, Thema, die wichtigsten Inhalte, das zentrale "
    "Ergebnis und die nächsten Schritte — selbsterklärend, ohne den Rest des "
    "Protokolls lesen zu müssen]\n\n"
    "### Besprochene Punkte\n"
    "- [Punkt 1]\n"
    "- [Punkt 2]\n\n"
    "### Entscheidungen\n"
    "- [Entscheidung 1 — kurz und präzise]\n\n"
    "### Offene Aufgaben\n"
    "- [Aufgabe] — Verantwortlich: [Name oder –], Deadline: [Datum oder –]\n\n"
    "### Nächster Termin\n"
    "[Datum/Uhrzeit und ggf. Anlass — nur falls genannt]"
)


class ProtokollWorkflow(BaseWorkflow):
    def __init__(
        self,
        settings,
        language: str = "de",
        backend: str = "online",
        local_model: str = "small",
        device: int | None = None,
        custom_terms: list[str] | None = None,
    ):
        super().__init__(WorkflowType.PROTOKOLL)
        self._settings = settings
        self._language = language
        self._backend = backend
        self._local_model = local_model
        self._custom_terms = custom_terms or []
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

    def import_file(self, path: str) -> None:
        self._set_phase(WorkflowPhase.PROCESSING, "Wird vorbereitet ...")
        threading.Thread(target=self._run_import, args=(path,), daemon=True).start()

    def _run_import(self, path: str) -> None:
        ext = os.path.splitext(path)[1].lower()
        try:
            if ext in AUDIO_EXTENSIONS:
                status = (
                    f"Wird lokal transkribiert ({self._local_model}) ..."
                    if self._backend == "local"
                    else "Wird transkribiert ..."
                )
                self._set_phase(WorkflowPhase.PROCESSING, status)
                raw, hint = transcribe_sync(
                    path, self._language, self._custom_terms,
                    self._backend, self._local_model,
                )
            elif ext in TEXT_EXTENSIONS:
                hint = ""
                with open(path, "r", encoding="utf-8") as f:
                    raw = f.read().strip()
                if not raw:
                    self._set_phase(WorkflowPhase.ERROR, error="Datei ist leer.")
                    return
            else:
                self._set_phase(WorkflowPhase.ERROR, error=f"Nicht unterstütztes Dateiformat: {ext}")
                return

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
            self._emit_output(protokoll)
        except Exception as e:
            self._set_phase(WorkflowPhase.ERROR, error=friendly_message(e))

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
                path, self._language, self._custom_terms,
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
            self._emit_output(protokoll)
        except Exception as e:
            self._set_phase(WorkflowPhase.ERROR, error=friendly_message(e))
            self._recorder.discard_recording()
