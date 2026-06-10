import threading
from typing import Callable
from pynput import keyboard

PressCallback = Callable[[], None]


class HotkeyService:
    """
    Global hotkey listener with press+release support for hold-to-record behavior.
    Combo format: 'ctrl+shift+r' (modifiers: ctrl, shift, alt; then the key char).
    """

    def __init__(self):
        self._bindings: dict[frozenset[str], tuple[PressCallback, PressCallback]] = {}
        self._active_mods: set[str] = set()
        self._active_chars: set[str] = set()
        self._triggered: set[frozenset[str]] = set()
        self._listener: keyboard.Listener | None = None
        self._lock = threading.Lock()

    def register(self, combo: str, on_press: PressCallback, on_release: PressCallback) -> None:
        key_set = self._parse(combo)
        self._bindings[key_set] = (on_press, on_release)

    def unregister_all(self) -> None:
        with self._lock:
            self._bindings.clear()

    def start(self) -> None:
        if self._listener:
            return
        self._listener = keyboard.Listener(
            on_press=self._on_down,
            on_release=self._on_up,
        )
        self._listener.daemon = True
        self._listener.start()

    def stop(self) -> None:
        if self._listener:
            self._listener.stop()
            self._listener = None

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _parse(combo: str) -> frozenset[str]:
        return frozenset(combo.lower().split("+"))

    def _current(self) -> frozenset[str]:
        return frozenset(self._active_mods | self._active_chars)

    def _on_down(self, key) -> None:
        mod = self._mod_name(key)
        char = self._char_name(key)
        triggers = []

        with self._lock:
            if mod:
                self._active_mods.add(mod)
            if char:
                self._active_chars.add(char)
            current = self._current()
            for combo, (cb_press, _) in self._bindings.items():
                if combo.issubset(current) and combo not in self._triggered:
                    self._triggered.add(combo)
                    triggers.append(cb_press)

        for cb in triggers:
            threading.Thread(target=cb, daemon=True).start()

    def _on_up(self, key) -> None:
        mod = self._mod_name(key)
        char = self._char_name(key)
        releases = []

        with self._lock:
            current_before = self._current()
            if mod:
                self._active_mods.discard(mod)
            if char:
                self._active_chars.discard(char)
            current_after = self._current()

            for combo in list(self._triggered):
                if not combo.issubset(current_after):
                    self._triggered.discard(combo)
                    if combo in self._bindings:
                        releases.append(self._bindings[combo][1])

        for cb in releases:
            threading.Thread(target=cb, daemon=True).start()

    @staticmethod
    def _mod_name(key) -> str | None:
        if not isinstance(key, keyboard.Key):
            return None
        name = key.name
        if "ctrl" in name:
            return "ctrl"
        if "shift" in name:
            return "shift"
        if "alt" in name:
            return "alt"
        return None

    @staticmethod
    def _char_name(key) -> str | None:
        if isinstance(key, keyboard.Key):
            return None
        try:
            char = key.char
            if not char:
                return None
            # When Ctrl is held pynput returns a control character instead of
            # the plain letter, e.g. Ctrl+R → '\x12' (ASCII 18).
            # Map it back: '\x01'=a … '\x1a'=z  (ord - 1 + ord('a'))
            if len(char) == 1 and ord(char) < 32:
                char = chr(ord(char) + ord("a") - 1)
            return char.lower()
        except AttributeError:
            return None
