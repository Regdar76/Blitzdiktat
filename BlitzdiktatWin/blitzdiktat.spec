# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec für Blitzdiktat (Windows).

Erstellt ein Standalone-Verzeichnis unter dist/Blitzdiktat/ mit:
  - Blitzdiktat.exe  (kein Konsolenfenster)
  - alle Python-Module, DLLs und Assets gebündelt

Verwendung:
  pyinstaller blitzdiktat.spec
"""

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_dynamic_libs,
    collect_submodules,
)
import sys, os

# ── Asset-Dateien ──────────────────────────────────────────────────────────────
datas = []

# customtkinter: Theme-JSON-Dateien und Bild-Assets
datas += collect_data_files("customtkinter", includes=["**/*.json", "**/*.png", "**/*.gif"])

# faster-whisper / ctranslate2: Vocabulary- und Config-Dateien der Modelle
# (eigentliche Modell-Gewichte werden zur Laufzeit in %APPDATA%\Blitzdiktat\ abgelegt)
try:
    datas += collect_data_files("faster_whisper", includes=["*.py"])
except Exception:
    pass

# tokenizers / huggingface_hub Konfigurationsdateien (falls vorhanden)
for pkg in ("tokenizers", "huggingface_hub"):
    try:
        datas += collect_data_files(pkg)
    except Exception:
        pass

# App-eigene Icon-Datei
_here = os.path.dirname(os.path.abspath(SPEC))
datas += [
    (os.path.join(_here, "resources", "blitzdiktat.ico"), "resources"),
]

# ── Native Bibliotheken ────────────────────────────────────────────────────────
binaries = []

# ctranslate2 bringt eigene BLAS-/OpenMP-DLLs mit
try:
    binaries += collect_dynamic_libs("ctranslate2")
except Exception:
    pass

# sounddevice bringt PortAudio mit
try:
    binaries += collect_dynamic_libs("sounddevice")
    binaries += collect_dynamic_libs("_sounddevice_data")
except Exception:
    pass

# ── Versteckte Imports ─────────────────────────────────────────────────────────
hiddenimports = [
    # tkinter
    "tkinter",
    "tkinter.ttk",
    "tkinter.messagebox",
    "tkinter.simpledialog",
    "_tkinter",
    # pynput – Windows-Backend explizit einbinden
    "pynput",
    "pynput.keyboard",
    "pynput.keyboard._win32",
    "pynput.mouse",
    "pynput.mouse._win32",
    # keyring – Windows Credential Manager
    "keyring",
    "keyring.backends",
    "keyring.backends.Windows",
    "keyring.backends.fail",
    "keyring.backends.null",
    # PIL / Pillow (für pystray und customtkinter)
    "PIL",
    "PIL.Image",
    "PIL.ImageTk",
    "PIL._tkinter_finder",
    # sounddevice
    "sounddevice",
    # pywin32
    "win32api",
    "win32con",
    "win32gui",
    "win32clipboard",
    "win32process",
    "pywintypes",
    # faster-whisper / ctranslate2
    "faster_whisper",
    "ctranslate2",
    # openai
    "openai",
    "openai.resources",
    "openai.resources.audio",
    "openai._streaming",
    # httpx / httpcore (openai nutzt diese)
    "httpx",
    "httpcore",
    "anyio",
    # numpy
    "numpy",
    # pystray
    "pystray",
    "pystray._win32",
    # reportlab (PDF-Erzeugung für Protokoll)
    "reportlab",
    "reportlab.lib",
    "reportlab.lib.pagesizes",
    "reportlab.lib.styles",
    "reportlab.lib.units",
    "reportlab.lib.colors",
    "reportlab.lib.enums",
    "reportlab.platypus",
    "reportlab.platypus.tables",
    "reportlab.pdfgen",
    "reportlab.pdfbase",
    "reportlab.pdfbase.ttfonts",
    "reportlab.pdfbase.pdfmetrics",
    # json / threading (Standardbibliothek, nur zur Sicherheit)
    "json",
    "threading",
    "queue",
    # App-eigene Workflow-Module (PyInstaller findet diese nicht automatisch)
    "features.workflows.transcription_workflow",
    "features.workflows.text_improvement_workflow",
    "features.workflows.dampf_ablassen_workflow",
    "features.workflows.emoji_text_workflow",
    "features.workflows.protokoll_workflow",
    "services.transcript_store",
]

# Alle Submodule von ctranslate2 und faster_whisper sicherstellen
for pkg in ("ctranslate2", "faster_whisper"):
    try:
        hiddenimports += collect_submodules(pkg)
    except Exception:
        pass

# Lokale App-Pakete vollständig einsammeln (features, services)
import sys as _sys
if _here not in _sys.path:
    _sys.path.insert(0, _here)
for pkg in ("features", "features.workflows", "features.tray", "features.ui", "services"):
    try:
        hiddenimports += collect_submodules(pkg)
    except Exception:
        pass

# ── Analyse ────────────────────────────────────────────────────────────────────
a = Analysis(
    ["main.py"],
    pathex=[_here],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Nicht benötigte, große Pakete ausschließen.
    # WICHTIG: pkg_resources._vendor NICHT ausschließen — aktuelles setuptools
    # lädt daraus zur Laufzeit jaraco.text; sonst stürzt die App beim Start ab
    # ("The 'jaraco.text' package is required").
    excludes=[
        "matplotlib",
        "scipy",
        "pandas",
        "IPython",
        "jupyter",
        "notebook",
        "pytest",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Blitzdiktat",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=["vcruntime*.dll", "msvcp*.dll", "python*.dll"],
    console=False,          # kein schwarzes Konsolenfenster
    icon=os.path.join(_here, "resources", "blitzdiktat.ico"),
    version=os.path.join(_here, "version_info.txt"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=["vcruntime*.dll", "msvcp*.dll", "python*.dll"],
    name="Blitzdiktat",
)
