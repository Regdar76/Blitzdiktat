# Copyright (c) 2026 Thorben Meier. MIT License.
"""
Blitzdiktat for Windows — entry point.
Run with:  python main.py
Or via:    run.bat
"""

import threading

import customtkinter as ctk
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
    ctk.set_appearance_mode(app_state.settings.appearance_mode)

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
