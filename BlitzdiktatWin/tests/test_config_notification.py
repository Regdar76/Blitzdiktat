# Copyright (c) 2026 Thorben Meier. MIT License.
"""Regressionstest: Hotkey ohne Konfiguration meldet sich statt zu schweigen."""

from app_state import AppState
from features.workflows.base_workflow import WorkflowType


def test_start_workflow_without_config_sets_notification(monkeypatch):
    state = AppState()
    monkeypatch.setattr(AppState, "is_configured", property(lambda self: False))

    notified = []
    state.subscribe(lambda s: notified.append(s.notification))

    state.start_workflow(WorkflowType.TRANSCRIPTION)

    assert state.active_workflow is None
    assert state.notification            # Meldung gesetzt (config_error-Text)
    assert notified and notified[-1]     # Subscriber wurden informiert
