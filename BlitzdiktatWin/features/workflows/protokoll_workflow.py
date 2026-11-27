# Copyright (c) 2026 Thorben Meier. MIT License.
import os
import threading

from services.transcription_service import transcribe_sync
from services import llm_service
from services.error_handler import friendly_message
from .base_workflow import WorkflowPhase, WorkflowType
from .recording_workflow import RecordingWorkflow

AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".aac", ".wma"}
TEXT_EXTENSIONS  = {".txt", ".md"}


def read_text_file(path: str) -> str:
    """Liest eine Textdatei tolerant: UTF-8 (inkl. BOM), dann cp1252.

    Deutsche .txt-Dateien aus Notepad/Word sind häufig cp1252-kodiert —
    striktes UTF-8 warf dafür einen UnicodeDecodeError.
    """
    for enc in ("utf-8-sig", "cp1252"):
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


# Rückwärtskompatibler Name; die Prompts liegen gesammelt in services/prompts.py.
from services.prompts import PROTOKOLL_SYSTEM_PROMPT  # noqa: F401


class ProtokollWorkflow(RecordingWorkflow):
    """Blitzdiktat Protokoll: Besprechung → strukturiertes Protokoll (+ PDF).

    Zusätzlich zum Aufnahme-Weg der Basisklasse gibt es den Datei-Import
    (Audio- oder Textdatei) über import_file().
    """

    PROCESS_STATUS = "Protokoll wird erstellt ..."

    def __init__(
        self,
        settings,
        language: str = "de",
        backend: str = "online",
        local_model: str = "small",
        device: int | None = None,
        custom_terms: list[str] | None = None,
    ):
        super().__init__(
            WorkflowType.PROTOKOLL,
            settings=settings,
            language=language,
            backend=backend,
            local_model=local_model,
            device=device,
            custom_terms=custom_terms or [],
        )

    def _process(self, raw: str) -> str:
        # Leer = eingebauter Prompt; welcher (OpenAI oder lokales Modell),
        # entscheidet llm_service anhand des gewählten KI-Anbieters.
        custom_prompt = getattr(self._settings, "system_prompt", "") or ""
        return self._run_async(llm_service.protokoll(raw, custom_prompt))

    # ------------------------------------------------------------------
    # Datei-Import (nur Protokoll)
    # ------------------------------------------------------------------

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
                    path, self._language, self._transcribe_terms(),
                    self._backend, self._local_model,
                )
            elif ext in TEXT_EXTENSIONS:
                hint = ""
                raw = read_text_file(path).strip()
                if not raw:
                    self._set_phase(WorkflowPhase.ERROR, error="Datei ist leer.")
                    return
            else:
                self._set_phase(WorkflowPhase.ERROR, error=f"Nicht unterstütztes Dateiformat: {ext}")
                return

            self._set_phase(WorkflowPhase.PROCESSING, self.PROCESS_STATUS)
            protokoll = self._process(raw)

            done_status = f"Fertig. ({hint})" if hint else "Fertig."
            self._set_phase(WorkflowPhase.DONE, status=done_status)
            self._emit_output(protokoll)
        except Exception as e:
            self._set_phase(WorkflowPhase.ERROR, error=friendly_message(e))
