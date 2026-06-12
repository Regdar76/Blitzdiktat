# Copyright (c) 2026 Thorben Meier. MIT License.
import wave
import os
import time
import threading
import datetime
import numpy as np
import sounddevice as sd

SAMPLE_RATE    = 16000
CHANNELS       = 1
MAX_AGE_DAYS   = 14


def recordings_dir() -> str:
    """Permanenter Ordner für alle Aufnahmen: %LOCALAPPDATA%\\Blitzdiktat\\Audioaufnahmen"""
    base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    path = os.path.join(base, "Blitzdiktat", "Audioaufnahmen")
    os.makedirs(path, exist_ok=True)
    return path


def cleanup_old_recordings() -> None:
    """Löscht WAV-Dateien im Aufnahmeordner, die älter als MAX_AGE_DAYS Tage sind."""
    folder = recordings_dir()
    cutoff = time.time() - MAX_AGE_DAYS * 86400
    try:
        for name in os.listdir(folder):
            if not name.lower().endswith(".wav"):
                continue
            path = os.path.join(folder, name)
            try:
                if os.path.getmtime(path) < cutoff:
                    os.remove(path)
            except Exception:
                pass
    except Exception:
        pass


def list_input_devices() -> list[tuple[int, str]]:
    """Gibt alle verfügbaren Eingabegeräte als (index, name) zurück."""
    result = []
    try:
        for i, dev in enumerate(sd.query_devices()):
            if dev["max_input_channels"] > 0:
                result.append((i, dev["name"]))
    except Exception:
        pass
    return result


def find_device_index(name: str) -> int | None:
    """Sucht den Index eines Geräts anhand des Namens. None = Systemstandard."""
    if not name:
        return None
    for idx, dev_name in list_input_devices():
        if dev_name == name:
            return idx
    return None


class AudioRecorder:
    def __init__(self, device: int | None = None):
        self._device = device
        self._frames: list[np.ndarray] = []
        self._recording = False
        self._stream: sd.InputStream | None = None
        self._lock = threading.Lock()
        self._start_time: float | None = None
        self._recording_path: str | None = None
        self.last_duration: float = 0.0
        self.audio_level: float = 0.0
        self.error_message: str | None = None

    @property
    def is_recording(self) -> bool:
        return self._recording

    @property
    def recording_path(self) -> str | None:
        return self._recording_path

    def start_recording(self) -> None:
        with self._lock:
            self._frames = []
            self._recording = True
            self._start_time = time.time()
            self._recording_path = None
            self.error_message = None
            self.audio_level = 0.0

        def _callback(indata, frames, time_info, status):
            with self._lock:
                if self._recording:
                    self._frames.append(indata.copy())
                    self.audio_level = float(np.sqrt(np.mean(indata ** 2)))

        try:
            self._stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype=np.float32,
                device=self._device,
                callback=_callback,
            )
            self._stream.start()
        except Exception as e:
            with self._lock:
                self._recording = False
            self.error_message = f"Mikrofon-Fehler: {e}"

    def stop_recording(self) -> None:
        with self._lock:
            if not self._recording:
                return
            self._recording = False
            if self._start_time:
                self.last_duration = time.time() - self._start_time
            self.audio_level = 0.0

        try:
            if self._stream:
                self._stream.stop()
                self._stream.close()
                self._stream = None
        except Exception:
            pass

        with self._lock:
            frames = list(self._frames)

        if frames:
            self._recording_path = self._save_wav(frames)

    def discard_recording(self) -> None:
        path = self._recording_path
        self._recording_path = None
        self._frames = []
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass

    def _save_wav(self, frames: list[np.ndarray]) -> str:
        data      = np.concatenate(frames, axis=0).flatten()
        data_int16 = (np.clip(data, -1.0, 1.0) * 32767).astype(np.int16)

        ts   = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        path = os.path.join(recordings_dir(), f"blitzdiktat_{ts}.wav")

        with wave.open(path, "w") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(data_int16.tobytes())

        return path
