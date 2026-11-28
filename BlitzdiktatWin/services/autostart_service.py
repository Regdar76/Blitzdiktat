# Copyright (c) 2026 Thorben Meier. MIT License.
"""
Blitzdiktat mit Windows starten – ein- und ausschaltbar.

Eintrag unter HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run (nur für
den angemeldeten Benutzer, keine Administratorrechte). Das Setup legt ihn bei
der ersten Installation an; bei Updates bleibt die Wahl des Nutzers erhalten.
"""

import os
import sys

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "Blitzdiktat"


def is_supported() -> bool:
    """Nur das installierte Programm kann sich eintragen – nicht `python main.py`."""
    return bool(getattr(sys, "frozen", False)) and os.name == "nt"


def _command() -> str:
    return f'"{sys.executable}"'


def is_enabled() -> bool:
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            value, _kind = winreg.QueryValueEx(key, VALUE_NAME)
        return bool(str(value).strip())
    except OSError:
        return False


def set_enabled(enabled: bool) -> bool:
    """Trägt den Autostart ein oder entfernt ihn. True = geschafft."""
    try:
        import winreg
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            if enabled:
                winreg.SetValueEx(key, VALUE_NAME, 0, winreg.REG_SZ, _command())
            else:
                try:
                    winreg.DeleteValue(key, VALUE_NAME)
                except FileNotFoundError:
                    pass
        return True
    except OSError:
        return False
