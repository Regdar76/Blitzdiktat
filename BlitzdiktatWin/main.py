# Copyright (c) 2026 Thorben Meier. MIT License.
"""
Blitzdiktat for Windows — entry point.
Run with:  python main.py
Or via:    run.bat
"""

import threading
import time

import customtkinter as ctk
from app_state import AppState
from features.tray.tray_app import TrayApp
from features.ui.main_window import MainWindow
from services import local_server
from services.audio_recorder import cleanup_old_recordings
from services.transcript_store import cleanup_old_transcripts
from services.local_transcription_service import start_preload
from version import __version__


def _cleanup_loop() -> None:
    """Aufnahmen und Transkriptionen löschen, die älter als 14 Tage sind – beim Start und
    danach alle sechs Stunden (ein Rechner, der nur schläft, räumte sonst nie auf)."""
    while True:
        for job in (cleanup_old_recordings, cleanup_old_transcripts):
            try:
                job()
            except Exception:
                pass
        time.sleep(6 * 3600)


def main() -> None:
    # Läuft Blitzdiktat schon (Autostart + Klick im Startmenü), nur dessen Fenster zeigen.
    from services import single_instance
    if not single_instance.acquire():
        return

    threading.Thread(target=_cleanup_loop, daemon=True, name="aufraeumen").start()

    # Small-Modell beim ersten Start vorausladen, damit es beim ersten Einsatz sofort bereit ist
    start_preload()

    app_state = AppState()
    ctk.set_appearance_mode(app_state.settings.appearance_mode)

    # Läuft die Text-KI über LM Studio auf diesem Rechner, dessen Server schon
    # jetzt starten – sonst wartet das erste Diktat darauf.
    # Die Einrichtung übernimmt alles: LM Studio und Modell nachholen, Server starten,
    # passendes Modell wählen. Ist sie aus (manuelle Wahl), bleibt es beim einfachen Start.
    from services import local_ai_setup
    if local_ai_setup.needs_local_ai(app_state.settings):
        app_state.start_local_ai_setup()
    elif app_state.settings.llm_provider == "custom":
        def start_local_ai() -> None:
            if local_server.ensure_running(app_state.settings.custom_llm_base_url):
                app_state.heal_local_model()

        threading.Thread(target=start_local_ai, daemon=True).start()

    main_window = MainWindow(app_state)
    single_instance.on_second_start(main_window.show)
    import app_state as app_state_module
    if app_state_module.LOAD_PROBLEM:
        app_state.notification = (
            "Die Einstellungen waren beschädigt und wurden zurückgesetzt. "
            "Die alte Datei liegt als settings.json.defekt im Blitzdiktat-Ordner."
        )
    if app_state.setup_busy():
        main_window.show()          # die Einrichtung läuft: Fortschritt sofort sichtbar machen

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
