# Copyright (c) 2026 Thorben Meier. MIT License.
"""
Lokale Offline-Transkription via faster-whisper (CTranslate2-Backend).
Modelle werden beim ersten Einsatz automatisch von HuggingFace geladen
und in %APPDATA%\\Blitzdiktat\\whisper_models gespeichert.
"""

import os
import threading

_IMPORT_ERROR: str = ""
try:
    from faster_whisper import WhisperModel
    AVAILABLE = True
except Exception as _e:
    AVAILABLE = False
    _IMPORT_ERROR = str(_e)

_CACHE: dict[str, "WhisperModel"] = {}
_LOCK = threading.Lock()

MODELS = [
    ("tiny",     "Tiny     (~75 MB)   — sehr schnell, weniger präzise"),
    ("base",     "Base     (~150 MB)  — schnell"),
    ("small",    "Small    (~500 MB)  — gute Balance  ✓ Empfohlen"),
    ("medium",   "Medium   (~1.5 GB)  — präzise"),
    ("large-v3", "Large-v3 (~3 GB)    — beste Qualität"),
]
MODEL_NAMES = [m[0] for m in MODELS]
DEFAULT_MODEL = "small"


def cache_dir() -> str:
    base = os.environ.get("APPDATA", os.path.expanduser("~"))
    return os.path.join(base, "Blitzdiktat", "whisper_models")


def is_model_cached(model_name: str) -> bool:
    d = os.path.join(cache_dir(), f"models--Systran--faster-whisper-{model_name}")
    return os.path.isdir(d)


def _load_model(model_name: str) -> "WhisperModel":
    if not AVAILABLE:
        detail = f": {_IMPORT_ERROR}" if _IMPORT_ERROR else ""
        raise RuntimeError(
            f"faster-whisper nicht verfügbar{detail}. "
            "Bitte 'pip install faster-whisper' ausführen und App neu starten."
        )
    # Lock hier statt beim Aufrufer: preload_default_model() lud sonst ohne
    # Lock — startete die erste Transkription während des Preloads, luden
    # beide Threads dasselbe Modell parallel (doppelter RAM, Race auf _CACHE).
    with _LOCK:
        if model_name not in _CACHE:
            os.makedirs(cache_dir(), exist_ok=True)
            _CACHE[model_name] = WhisperModel(
                model_name,
                device="cpu",
                compute_type="int8",
                download_root=cache_dir(),
            )
        return _CACHE[model_name]


def transcribe_local(
    audio_path: str,
    model_name: str = DEFAULT_MODEL,
    language: str = "de",
    custom_terms: list[str] | None = None,
) -> str:
    model = _load_model(model_name)

    kwargs: dict = {"language": language, "beam_size": 5}
    from . import vocabulary_service
    hints = vocabulary_service.prompt_terms(custom_terms or [])
    if hints:
        # "hotwords" wirkt in jedem 30-Sekunden-Abschnitt, "initial_prompt" nur im ersten –
        # bei langen Aufnahmen (Protokoll) ginge der Hinweis sonst verloren.
        kwargs["hotwords"] = ", ".join(hints)

    segments, _ = model.transcribe(audio_path, **kwargs)
    return " ".join(seg.text.strip() for seg in segments).strip()


def evict_model(model_name: str) -> None:
    with _LOCK:
        _CACHE.pop(model_name, None)


_PRELOADING = False


def is_preloading() -> bool:
    """True, solange das Standardmodell heruntergeladen wird (App noch nicht benutzbar)."""
    return _PRELOADING


def start_preload() -> None:
    """Startet das Vorladen im Hintergrund. Fehlt das Modell, gilt die App sofort als
    "noch in Einrichtung" – nicht erst, wenn der Thread läuft."""
    global _PRELOADING
    if AVAILABLE and not is_model_cached(DEFAULT_MODEL):
        _PRELOADING = True
    threading.Thread(target=preload_default_model, daemon=True, name="whisper-preload").start()


def preload_default_model() -> None:
    """Lädt das Small-Modell im Hintergrund vor, damit es beim ersten Einsatz sofort verfügbar ist."""
    global _PRELOADING
    if not AVAILABLE:
        _PRELOADING = False
        return
    if not is_model_cached(DEFAULT_MODEL):
        _PRELOADING = True
        try:
            _load_model(DEFAULT_MODEL)
        except Exception:
            pass
    _PRELOADING = False
