"""
Blitzdiktat for Windows — entry point.
Run with:  python main.py
Or via:    run.bat
"""

import sys
import os

# ── Ensure all required packages are on sys.path ────────────────────────────
# Priority 1: local "packages/" folder next to this script — always works,
# independent of user profiles, roaming AppData, or network drives.
_here = os.path.dirname(os.path.abspath(__file__))
_local_pkgs = os.path.join(_here, "packages")
if os.path.isdir(_local_pkgs) and _local_pkgs not in sys.path:
    sys.path.insert(0, _local_pkgs)

# Priority 2: user-level site-packages (may be inaccessible in some environments)
try:
    import site as _site
    _u = _site.getusersitepackages()
    if _u and os.path.isdir(_u) and _u not in sys.path:
        sys.path.insert(0, _u)
except Exception:
    pass
_appdata = os.environ.get("APPDATA", "")
if _appdata:
    _ver = f"Python{sys.version_info.major}{sys.version_info.minor}"
    _roaming = os.path.join(_appdata, "Python", _ver, "site-packages")
    if os.path.isdir(_roaming) and _roaming not in sys.path:
        sys.path.insert(0, _roaming)

import threading

from app_state import AppState
from features.tray.tray_app import TrayApp
from features.ui.main_window import MainWindow
from services.audio_recorder import cleanup_old_recordings
from services.transcript_store import cleanup_old_transcripts
from services.local_transcription_service import preload_default_model
from version import __version__


def main() -> None:
    # Aufnahmen und Transkriptionen löschen, die älter als 14 Tage sind (im Hintergrund)
    threading.Thread(target=cleanup_old_recordings, daemon=True).start()
    threading.Thread(target=cleanup_old_transcripts, daemon=True).start()

    # Small-Modell beim ersten Start vorausladen, damit es beim ersten Einsatz sofort bereit ist
    threading.Thread(target=preload_default_model, daemon=True).start()

    app_state = AppState()

    main_window = MainWindow(app_state)

    tray = TrayApp(
        app_state,
        on_show_window=main_window.show,
        on_quit=main_window.quit,
    )

    tray_thread = threading.Thread(target=tray.run, daemon=True)
    tray_thread.start()

    app_state.bind_hotkeys()

    is_new_version = app_state.settings.last_seen_version != __version__
    if not app_state.settings.has_seen_onboarding or is_new_version:
        app_state.settings.has_seen_onboarding = True
        app_state.settings.last_seen_version = __version__
        app_state.save_settings()
        main_window.show()

    main_window.mainloop()

    app_state.hotkey_service.stop()
    tray.stop()


if __name__ == "__main__":
    main()
