# Copyright (c) 2026 Thorben Meier. MIT License.
"""Regressionstests für das Cancel-Verhalten von BaseWorkflow.

Hintergrund: Ein Workflow-Wechsel während PROCESSING ließ den alten
Verarbeitungs-Thread weiterlaufen; sein Output wurde verspätet eingefügt.
cancel() koppelt Callbacks ab und unterdrückt Phase/Output dauerhaft.
"""

from features.workflows.base_workflow import (
    BaseWorkflow,
    WorkflowPhase,
    WorkflowType,
)


class _DummyWorkflow(BaseWorkflow):
    def __init__(self):
        super().__init__(WorkflowType.TRANSCRIPTION)

    def start(self) -> None:
        self._set_phase(WorkflowPhase.RECORDING)

    def stop(self) -> None:
        self._set_phase(WorkflowPhase.PROCESSING)

    def reset(self) -> None:
        self._set_phase(WorkflowPhase.IDLE)


def test_emit_output_reaches_callback_when_active():
    wf = _DummyWorkflow()
    received = []
    wf.on_output = received.append

    wf._emit_output("hallo")

    assert received == ["hallo"]


def test_cancel_suppresses_output():
    wf = _DummyWorkflow()
    received = []
    wf.on_output = received.append

    wf.cancel()
    wf._emit_output("zu spät")

    assert received == []
    assert wf.on_output is None


def test_cancel_suppresses_phase_changes():
    wf = _DummyWorkflow()
    wf.start()
    assert wf.state.phase == WorkflowPhase.RECORDING

    states = []
    wf.on_state_change = states.append
    wf.cancel()
    wf.stop()

    assert states == []
    assert wf.state.phase == WorkflowPhase.RECORDING  # eingefroren, kein Update mehr


def test_reset_after_cancel_does_not_notify():
    wf = _DummyWorkflow()
    notified = []
    wf.on_state_change = lambda s: notified.append(s.phase)

    wf.start()
    wf.cancel()
    wf.reset()

    assert notified == [WorkflowPhase.RECORDING]
