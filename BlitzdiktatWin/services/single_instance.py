# Copyright (c) 2026 Thorben Meier. MIT License.
"""
Blitzdiktat darf nur einmal laufen.

Mit Autostart und einem zusätzlichen Klick im Startmenü liefen sonst zwei
Programme: Jedes Tastenkürzel nahm doppelt auf und fügte den Text zweimal ein.
Die zweite Instanz bittet die erste, ihr Fenster zu zeigen, und beendet sich.
"""

import ctypes
import threading
from typing import Callable

_MUTEX_NAME = "Local\\Blitzdiktat-Instanz"
_EVENT_NAME = "Local\\Blitzdiktat-Fenster-zeigen"
_ERROR_ALREADY_EXISTS = 183
_WAIT_OBJECT_0 = 0

_handles: list[int] = []          # offen halten, solange das Programm läuft


def _kernel32():
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.CreateMutexW.restype = ctypes.c_void_p
    k.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
    k.CreateEventW.restype = ctypes.c_void_p
    k.CreateEventW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_bool, ctypes.c_wchar_p]
    k.SetEvent.argtypes = [ctypes.c_void_p]
    k.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    k.CloseHandle.argtypes = [ctypes.c_void_p]
    return k


def acquire(mutex_name: str = _MUTEX_NAME, event_name: str = _EVENT_NAME) -> bool:
    """True = wir sind die einzige Instanz. False = es läuft schon eine; sie wurde gebeten,
    ihr Fenster zu zeigen."""
    try:
        k = _kernel32()
        mutex = k.CreateMutexW(None, False, mutex_name)
        already = ctypes.get_last_error() == _ERROR_ALREADY_EXISTS
        if mutex and not already:
            _handles.append(mutex)
            return True
        event = k.CreateEventW(None, False, False, event_name)
        if event:
            k.SetEvent(event)
            k.CloseHandle(event)
        if mutex:
            k.CloseHandle(mutex)
        return False
    except Exception:
        return True               # im Zweifel starten statt den Nutzer auszusperren


def on_second_start(callback: Callable[[], None], event_name: str = _EVENT_NAME) -> None:
    """Ruft ``callback`` auf, sobald jemand Blitzdiktat ein zweites Mal startet."""
    try:
        k = _kernel32()
        event = k.CreateEventW(None, False, False, event_name)
        if not event:
            return
        _handles.append(event)
    except Exception:
        return

    def wait() -> None:
        while True:
            if k.WaitForSingleObject(event, 0xFFFFFFFF) != _WAIT_OBJECT_0:
                return
            try:
                callback()
            except Exception:
                pass

    threading.Thread(target=wait, daemon=True, name="zweitstart").start()
