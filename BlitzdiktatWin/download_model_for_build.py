"""
Lädt das Whisper-Small-Modell in dist\whisper_models\ herunter,
damit der Inno-Setup-Installer es direkt mitbündeln kann.
Wird nur vom Build-Script aufgerufen, nicht von der App selbst.
"""

import os, sys

_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_here, "packages"))

target = os.path.join(_here, "dist", "whisper_models")
os.makedirs(target, exist_ok=True)

print(f"Lade Whisper-Small-Modell nach {target} ...")
try:
    from faster_whisper import WhisperModel
    WhisperModel("small", device="cpu", compute_type="int8", download_root=target)
    print("OK – Modell heruntergeladen.")
except Exception as e:
    print(f"FEHLER beim Download: {e}")
    sys.exit(1)
