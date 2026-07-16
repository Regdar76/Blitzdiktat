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
    """Nimmt vom Mikrofon auf und schreibt direkt streamend in die WAV-Datei.

    Früher wurden alle Frames im RAM gesammelt und erst beim Stoppen
    zusammengefügt — eine Stunde Protokoll-Aufnahme brauchte so >500 MB
    Spitzenspeicher. Jetzt hält der Recorder nur den aktuellen Block.
    """

    def __init__(self, device: int | None = None):
        self._device = device
        self._recording = False
        self._stream: sd.InputStream | None = None
        self._lock = threading.Lock()
        self._start_time: float | None = None
        self._recording_path: str | None = None
        self._wave: wave.Wave_write | None = None
        self._wave_path: str | None = None
        self._frames_written = 0
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
        ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        path = os.path.join(recordings_dir(), f"blitzdiktat_{ts}.wav")

        with self._lock:
            self._start_time = time.time()
            self._recording_path = None
            self._frames_written = 0
            self.error_message = None
            self.audio_level = 0.0
            try:
                wf = wave.open(path, "wb")
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(2)
                wf.setframerate(SAMPLE_RATE)
            except Exception as e:
                self._recording = False
                self.error_message = f"Aufnahmedatei konnte nicht angelegt werden: {e}"
                return
            self._wave = wf
            self._wave_path = path
            self._recording = True

        def _callback(indata, frames, time_info, status):
            self._on_audio(indata, frames)

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
                self._close_wave_locked(discard=True)
            self.error_message = f"Mikrofon-Fehler: {e}"

    def _on_audio(self, indata: np.ndarray, frames: int) -> None:
        # Konvertierung außerhalb des Locks — im Lock nur der Dateizugriff.
        data_int16 = (np.clip(indata, -1.0, 1.0) * 32767).astype(np.int16)
        level = float(np.sqrt(np.mean(indata ** 2)))
        with self._lock:
            if not self._recording or self._wave is None:
                return
            try:
                self._wave.writeframes(data_int16.tobytes())
                self._frames_written += frames
                self.audio_level = level
            except Exception as e:
                # Platte voll o. ä.: Datei verwerfen, Fehler merken. is_recording
                # bleibt True, damit der Workflow den Stopp regulär durchläuft
                # und den Fehler beim Verarbeiten meldet (statt in RECORDING
                # hängen zu bleiben).
                self.error_message = f"Aufnahme-Schreibfehler: {e}"
                self._close_wave_locked(discard=True)

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
            path = self._wave_path
            ok = (
                self._wave is not None
                and self._frames_written > 0
                and self.error_message is None
            )
            self._close_wave_locked(discard=not ok)
            if ok:
                self._recording_path = path

    def discard_recording(self) -> None:
        with self._lock:
            self._close_wave_locked(discard=True)
            path = self._recording_path
            self._recording_path = None
            self._frames_written = 0
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass

    def _close_wave_locked(self, discard: bool) -> None:
        """Schließt die offene WAV-Datei; nur mit gehaltenem self._lock aufrufen."""
        wf, path = self._wave, self._wave_path
        self._wave = None
        self._wave_path = None
        if wf is not None:
            try:
                wf.close()
            except Exception:
                pass
        if discard and path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass
