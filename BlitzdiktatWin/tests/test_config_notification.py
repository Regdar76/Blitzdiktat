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


def test_ki_funktion_ohne_text_ki_meldet_sich_vor_der_aufnahme(monkeypatch):
    """Lokale Transkription + fehlender API Key fiel früher erst nach dem Sprechen auf."""
    from services import llm_service

    state = AppState()
    monkeypatch.setattr(AppState, "is_configured", property(lambda self: True))
    monkeypatch.setattr(llm_service, "config_problem", lambda: "API Key fehlt — Einstellungen öffnen")

    state.start_workflow(WorkflowType.TEXT_IMPROVER)

    assert state.active_workflow is None
    assert state.notification == "API Key fehlt — Einstellungen öffnen"


def test_protokoll_import_ohne_text_ki_meldet_sich(monkeypatch):
    from services import llm_service

    state = AppState()
    monkeypatch.setattr(AppState, "is_configured", property(lambda self: True))
    monkeypatch.setattr(llm_service, "config_problem", lambda: "Eigener KI-Server: kein Modell gewählt")

    state.import_file_for_protokoll("besprechung.txt")

    assert state.active_workflow is None
    assert state.notification == "Eigener KI-Server: kein Modell gewählt"
