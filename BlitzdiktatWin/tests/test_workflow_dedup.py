# Copyright (c) 2026 Thorben Meier. MIT License.
"""Tests für die gemeinsame RecordingWorkflow-Basisklasse (Dedup-Refactor)."""

from types import SimpleNamespace

from features.workflows.base_workflow import WorkflowType
from features.workflows.recording_workflow import RecordingWorkflow
from features.workflows.transcription_workflow import TranscriptionWorkflow
from features.workflows.text_improvement_workflow import TextImprovementWorkflow
from features.workflows.dampf_ablassen_workflow import DampfAblassenWorkflow
from features.workflows.emoji_text_workflow import EmojiTextWorkflow
from features.workflows.protokoll_workflow import ProtokollWorkflow


def test_all_workflows_share_recording_base():
    assert issubclass(TranscriptionWorkflow, RecordingWorkflow)
    assert issubclass(TextImprovementWorkflow, RecordingWorkflow)
    assert issubclass(DampfAblassenWorkflow, RecordingWorkflow)
    assert issubclass(EmojiTextWorkflow, RecordingWorkflow)
    assert issubclass(ProtokollWorkflow, RecordingWorkflow)


def test_workflow_types_wired_correctly():
    s = SimpleNamespace()
    assert TranscriptionWorkflow().workflow_type == WorkflowType.TRANSCRIPTION
    assert TextImprovementWorkflow(s).workflow_type == WorkflowType.TEXT_IMPROVER
    assert DampfAblassenWorkflow(s).workflow_type == WorkflowType.DAMPF_ABLASSEN
    assert EmojiTextWorkflow(s).workflow_type == WorkflowType.EMOJI_TEXT
    assert ProtokollWorkflow(s).workflow_type == WorkflowType.PROTOKOLL


def test_transcription_process_applies_voice_commands():
    wf = TranscriptionWorkflow()
    assert wf.PROCESS_STATUS is None
    assert "\n" in wf._process("erster Punkt Absatz zweiter Punkt")


def test_transcribe_terms_explicit_beats_settings():
    wf = TranscriptionWorkflow(custom_terms=["Karstens", "Blitzdiktat"])
    assert wf._transcribe_terms() == ["Karstens", "Blitzdiktat"]

    # Explizit leere Liste bleibt leer (None wäre "aus Settings ableiten")
    assert TranscriptionWorkflow(custom_terms=[])._transcribe_terms() == []


def test_transcribe_terms_falls_back_to_settings():
    settings = SimpleNamespace(custom_terms=["HK", "Kiel"])
    wf = TextImprovementWorkflow(settings)
    assert wf._transcribe_terms() == ["HK", "Kiel"]

    # Settings ohne custom_terms (Dampf/Emoji) → leere Liste
    assert DampfAblassenWorkflow(SimpleNamespace())._transcribe_terms() == []


def test_llm_workflows_define_process_status():
    assert TextImprovementWorkflow(SimpleNamespace()).PROCESS_STATUS
    assert DampfAblassenWorkflow(SimpleNamespace()).PROCESS_STATUS
    assert EmojiTextWorkflow(SimpleNamespace()).PROCESS_STATUS
    assert ProtokollWorkflow(SimpleNamespace()).PROCESS_STATUS
