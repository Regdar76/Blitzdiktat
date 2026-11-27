# Copyright (c) 2026 Thorben Meier. MIT License.
"""
Startet den Server von LM Studio, wenn die Text-KI auf diesem Rechner läuft.

LM Studio beantwortet Anfragen nur, solange sein Server läuft – nach einem
Neustart des Rechners ist er aus. Damit niemand daran denken muss, startet
Blitzdiktat ihn bei Bedarf selbst über das mitgelieferte Hilfsprogramm "lms".
Für Server auf anderen Rechnern oder andere Programme passiert hier nichts.
"""

import glob
import os
import socket
import subprocess
import threading
import time
from urllib.parse import urlparse

_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
_RETRY_PAUSE = 60.0          # nach einem Fehlversuch nicht sofort wieder starten
_lock = threading.Lock()
_last_failure = 0.0


def host_and_port(base_url: str) -> tuple[str, int]:
    parsed = urlparse(base_url if "://" in base_url else "http://" + base_url)
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    return (parsed.hostname or "").lower(), port


def is_local_url(base_url: str) -> bool:
    return host_and_port(base_url)[0] in _LOCAL_HOSTS


def is_reachable(base_url: str, timeout: float = 1.5) -> bool:
    host, port = host_and_port(base_url)
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def find_lms() -> str | None:
    """Sucht das Hilfsprogramm von LM Studio (im Profil oder im Programmordner)."""
    home = os.path.expanduser("~")
    candidates = [os.path.join(home, ".lmstudio", "bin", "lms.exe")]
    local = os.environ.get("LOCALAPPDATA", "")
    if local:
        # Liegt schon direkt nach der Installation vor, noch bevor LM Studio
        # zum ersten Mal geöffnet wurde.
        candidates += sorted(glob.glob(
            os.path.join(local, "Programs", "*", "resources", "app", ".webpack*", "lms.exe")
        ))
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


def ensure_running(base_url: str, wait: float = 90.0) -> bool:
    """Sorgt dafür, dass der lokale Server antwortet. True = erreichbar."""
    global _last_failure
    if not is_local_url(base_url):
        return False
    if is_reachable(base_url):
        return True
    with _lock:
        if is_reachable(base_url):          # ein anderer Aufruf war schneller
            return True
        if time.monotonic() - _last_failure < _RETRY_PAUSE and _last_failure:
            return False
        lms = find_lms()
        if lms and _start(lms, host_and_port(base_url)[1]) and _wait_until_reachable(base_url, wait):
            return True
        _last_failure = time.monotonic()
        return False


def _start(lms: str, port: int) -> bool:
    try:
        subprocess.run(
            [lms, "server", "start", "--port", str(port)],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=120, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return True
    except (OSError, subprocess.SubprocessError):
        return False


def _wait_until_reachable(base_url: str, wait: float) -> bool:
    deadline = time.monotonic() + wait
    while time.monotonic() < deadline:
        if is_reachable(base_url):
            return True
        time.sleep(1.0)
    return False
