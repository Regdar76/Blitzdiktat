# Copyright (c) 2026 Thorben Meier. MIT License.
"""Aufnahmen müssen sich für die lokale Transkription einlesen lassen.

Regression: Mit av 19 scheiterte jede Aufnahme mit
"open() got an unexpected keyword argument 'metadata_errors'", weil
faster-whisper diesen Parameter an av.open() übergibt.
"""

import math
import struct
import wave

import pytest

pytest.importorskip("faster_whisper")
pytest.importorskip("av")


def test_aufnahme_wird_von_faster_whisper_eingelesen(tmp_path):
    from faster_whisper.audio import decode_audio

    path = tmp_path / "probe.wav"
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"".join(struct.pack("<h", int(3000 * math.sin(i / 20))) for i in range(16000)))

    audio = decode_audio(str(path), sampling_rate=16000)
    assert audio.shape == (16000,)
