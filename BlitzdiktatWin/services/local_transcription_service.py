"""
Lokale Offline-Transkription via faster-whisper (CTranslate2-Backend).
Modelle werden beim ersten Einsatz automatisch von HuggingFace geladen
und in %APPDATA%\\Blitzdiktat\\whisper_models gespeichert.
"""

import os
import sys
import threading

# ── Belt-and-suspenders: add packages to sys.path ──────────────────────────
# Priority 1: local packages/ dir next to main.py (always accessible,
# independent of user profile, roaming AppData, or network drives)
_here = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "packages"))
if os.path.isdir(_here) and _here not in sys.path:
    sys.path.insert(0, _here)

# Priority 2: user site-packages via Python API
try:
    import site as _site
    _u = _site.getusersitepackages()
    if _u and os.path.isdir(_u) and _u not in sys.path:
        sys.path.insert(0, _u)
except Exception:
    pass

# Priority 3: manual APPDATA fallback
_appdata = os.environ.get("APPDATA", "")
if _appdata:
    _manual = os.path.join(_appdata, "Python", f"Python{sys.version_info.major}{sys.version_info.minor}", "site-packages")
    if os.path.isdir(_manual) and _manual not in sys.path:
        sys.path.insert(0, _manual)

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
    with _LOCK:
        model = _load_model(model_name)

    kwargs: dict = {"language": language, "beam_size": 5}
    if custom_terms:
        kwargs["initial_prompt"] = ", ".join(custom_terms)

    segments, _ = model.transcribe(audio_path, **kwargs)
    return " ".join(seg.text.strip() for seg in segments).strip()


def evict_model(model_name: str) -> None:
    with _LOCK:
        _CACHE.pop(model_name, None)


def preload_default_model() -> None:
    """Lädt das Small-Modell im Hintergrund vor, damit es beim ersten Einsatz sofort verfügbar ist."""
    if not AVAILABLE:
        return
    if not is_model_cached(DEFAULT_MODEL):
        try:
            _load_model(DEFAULT_MODEL)
        except Exception:
            pass
