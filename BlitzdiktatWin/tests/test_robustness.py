# Copyright (c) 2026 Thorben Meier. MIT License.
"""Regressionstests für die Robustheits-Fixes:

- AudioRecorder schreibt streamend in die WAV-Datei (kein RAM-Puffer mehr)
- Online-Transkription prüft das 25-MB-Limit der OpenAI-API vorab
- Protokoll-Textimport liest auch cp1252-kodierte Dateien
"""

import os
import wave

import numpy as np
import pytest

from features.workflows.protokoll_workflow import read_text_file
from services import transcription_service
from services.audio_recorder import AudioRecorder, SAMPLE_RATE


# ── AudioRecorder: streamendes Schreiben ──────────────────────────────


def _fake_chunk(num_frames: int = 1024) -> np.ndarray:
    t = np.linspace(0, 1, num_frames, dtype=np.float32).reshape(-1, 1)
    return np.sin(2 * np.pi * 440 * t) * 0.5


def _open_for_test(recorder: AudioRecorder, tmp_path) -> str:
    """Öffnet die WAV-Datei wie start_recording, aber ohne Mikrofon-Stream."""
    path = str(tmp_path / "test_recording.wav")
    with recorder._lock:
        recorder._start_time = 0.0
        recorder._recording_path = None
        recorder._frames_written = 0
        recorder.error_message = None
        wf = wave.open(path, "wb")
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        recorder._wave = wf
        recorder._wave_path = path
        recorder._recording = True
    return path


def test_recorder_streams_chunks_to_wav(tmp_path):
    rec = AudioRecorder()
    path = _open_for_test(rec, tmp_path)

    for _ in range(5):
        chunk = _fake_chunk()
        rec._on_audio(chunk, len(chunk))
    rec.stop_recording()

    assert rec.recording_path == path
    assert rec.error_message is None
    with wave.open(path, "rb") as wf:
        assert wf.getnframes() == 5 * 1024
        assert wf.getframerate() == SAMPLE_RATE


def test_recorder_discards_empty_recording(tmp_path):
    rec = AudioRecorder()
    path = _open_for_test(rec, tmp_path)

    rec.stop_recording()   # kein einziger Frame geschrieben

    assert rec.recording_path is None
    assert not os.path.exists(path)


def test_recorder_write_error_keeps_recording_state_and_discards(tmp_path):
    rec = AudioRecorder()
    path = _open_for_test(rec, tmp_path)

    # Datei unter dem Recorder wegschließen → writeframes wirft
    rec._wave.close()

    chunk = _fake_chunk()
    rec._on_audio(chunk, len(chunk))

    # is_recording bleibt True, damit der Workflow den Stopp regulär
    # durchläuft und den Fehler meldet (statt in RECORDING zu hängen)
    assert rec.is_recording
    assert rec.error_message is not None

    rec.stop_recording()
    assert rec.recording_path is None
    assert not os.path.exists(path)


def test_recorder_discard_while_open(tmp_path):
    rec = AudioRecorder()
    path = _open_for_test(rec, tmp_path)
    chunk = _fake_chunk()
    rec._on_audio(chunk, len(chunk))

    rec.discard_recording()

    assert rec.recording_path is None
    assert not os.path.exists(path)


# ── 25-MB-Limit der Online-Transkription ──────────────────────────────


def test_exceeds_online_limit(tmp_path, monkeypatch):
    f = tmp_path / "audio.wav"
    f.write_bytes(b"x")

    assert not transcription_service.exceeds_online_limit(str(f))

    monkeypatch.setattr(
        transcription_service.os.path, "getsize",
        lambda _: transcription_service.OPENAI_MAX_UPLOAD_BYTES + 1,
    )
    assert transcription_service.exceeds_online_limit(str(f))


def test_exceeds_online_limit_missing_file():
    assert not transcription_service.exceeds_online_limit("gibt-es-nicht.wav")


def test_transcribe_sync_rejects_oversized_online(tmp_path, monkeypatch):
    f = tmp_path / "audio.wav"
    f.write_bytes(b"x")
    monkeypatch.setattr(
        transcription_service, "exceeds_online_limit", lambda _: True
    )
    # Lokales Backend im Test nicht verfügbar erzwingen
    import services.local_transcription_service as lts
    monkeypatch.setattr(lts, "AVAILABLE", False)

    with pytest.raises(RuntimeError, match="25 MB"):
        transcription_service.transcribe_sync(str(f), backend="online")


# ── Protokoll-Import: Encoding-Fallback ───────────────────────────────


def test_read_text_file_utf8(tmp_path):
    f = tmp_path / "utf8.txt"
    f.write_text("Besprechung über Maßnahmen", encoding="utf-8")
    assert read_text_file(str(f)) == "Besprechung über Maßnahmen"


def test_read_text_file_utf8_bom(tmp_path):
    f = tmp_path / "bom.txt"
    f.write_bytes("Besprechung".encode("utf-8-sig"))
    assert read_text_file(str(f)) == "Besprechung"


def test_read_text_file_cp1252(tmp_path):
    f = tmp_path / "ansi.txt"
    f.write_bytes("Besprechung über Maßnahmen — Rückbau".encode("cp1252"))
    assert read_text_file(str(f)) == "Besprechung über Maßnahmen — Rückbau"
