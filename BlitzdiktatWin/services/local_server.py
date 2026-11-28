# Copyright (c) 2026 Thorben Meier. MIT License.
"""
Startet den Server von LM Studio, wenn die Text-KI auf diesem Rechner läuft.

LM Studio beantwortet Anfragen nur, solange sein Server läuft – nach einem
Neustart des Rechners ist er aus. Damit niemand daran denken muss, startet
Blitzdiktat ihn bei Bedarf selbst. Das geschieht in Stufen, damit der Nutzer
nie von Hand eingreifen muss:

  1. Hilfsprogramm "lms" (``lms server start``).
  2. Hilft das nicht (z. B. nach der ersten Installation, wenn LM Studio noch
     nie geöffnet war, oder wenn "lms" fehlt): LM Studio selbst im Hintergrund
     öffnen, kurz warten und den Server dann erneut starten.
  3. Läuft der Server, aber das Modell ist nicht geladen: mit ausreichender
     Kontextlänge laden.

Für Server auf anderen Rechnern oder andere Programme passiert hier nichts.
"""

import glob
import json
import os
import shutil
import socket
import subprocess
import threading
import time
from dataclasses import dataclass
from urllib.parse import urlparse

_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
_RETRY_PAUSE = 60.0          # nach einem Fehlversuch nicht sofort wieder starten
_AFTER_LAUNCH_FIRST = 8.0    # Sekunden nach dem Öffnen von LM Studio bis zum ersten Server-Start
_AFTER_LAUNCH_SECOND = 40.0
CONTEXT_LENGTH = 8192       # Mindestlänge, damit lange Protokolle nicht abgeschnitten werden
_lock = threading.Lock()
_last_failure = 0.0
_last_reason = ""
_loaded_ok: set[str] = set()  # Modelle, die in dieser Sitzung schon geladen vorgefunden wurden


@dataclass
class StartResult:
    ok: bool
    reason: str = ""          # verständliche Meldung, wenn nicht ok

    def __bool__(self) -> bool:
        return self.ok


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


# ── LM Studio finden ────────────────────────────────────────────────────────

def _program_dirs() -> list[str]:
    dirs = []
    for var in ("LOCALAPPDATA",):
        base = os.environ.get(var, "")
        if base:
            dirs.append(os.path.join(base, "Programs"))
    for var in ("ProgramFiles", "ProgramFiles(x86)"):
        base = os.environ.get(var, "")
        if base:
            dirs.append(base)
    return dirs


def find_lms() -> str | None:
    """Sucht das Hilfsprogramm von LM Studio (im Profil oder im Programmordner)."""
    home = os.path.expanduser("~")
    candidates = [os.path.join(home, ".lmstudio", "bin", "lms.exe")]
    for base in _program_dirs():
        # Liegt schon direkt nach der Installation vor, noch bevor LM Studio
        # zum ersten Mal geöffnet wurde.
        candidates += sorted(glob.glob(
            os.path.join(base, "*", "resources", "app", ".webpack*", "lms.exe")
        ))
    for path in candidates:
        if os.path.isfile(path):
            return path
    # Bewusst keine Suche über PATH: Sie schließt den aktuellen Ordner ein, und dort
    # könnte ein fremdes "lms.exe" liegen.
    return None


def find_app() -> str | None:
    """Sucht das Programm "LM Studio" selbst (für den Notfall-Start)."""
    for base in _program_dirs():
        for pattern in ("LM Studio", "LM-Studio", "LMStudio", "*"):
            for path in sorted(glob.glob(os.path.join(base, pattern, "LM Studio.exe"))):
                return path
    return None


# ── Server starten ──────────────────────────────────────────────────────────

def ensure_running(base_url: str, wait: float = 90.0, force: bool = False) -> bool:
    """Sorgt dafür, dass der lokale Server antwortet. True = erreichbar."""
    return start_local_server(base_url, wait, force).ok


def last_reason() -> str:
    """Warum der letzte Startversuch scheiterte (leer, wenn nichts bekannt)."""
    return _last_reason


def start_local_server(base_url: str, wait: float = 90.0, force: bool = False) -> StartResult:
    """Wie ensure_running, liefert aber bei Misserfolg eine verständliche Begründung.

    force=True ignoriert die Pause nach einem früheren Fehlversuch (für den
    Knopf in den Einstellungen).
    """
    global _last_failure, _last_reason
    if not is_local_url(base_url):
        return StartResult(False, "Der Server läuft nicht auf diesem Rechner.")
    if is_reachable(base_url):
        return StartResult(True)
    with _lock:
        if is_reachable(base_url):          # ein anderer Aufruf war schneller
            return StartResult(True)
        if not force and _last_failure and time.monotonic() - _last_failure < _RETRY_PAUSE:
            return StartResult(False, _last_reason)
        reason = _start_in_stages(base_url, wait)
        if reason is None:
            _last_reason = ""
            return StartResult(True)
        _last_failure = time.monotonic()
        _last_reason = reason
        return StartResult(False, reason)


def _start_in_stages(base_url: str, wait: float) -> str | None:
    """None = Server läuft jetzt, sonst die Begründung des Misserfolgs."""
    port = host_and_port(base_url)[1]
    deadline = time.monotonic() + wait

    def remaining() -> float:
        return max(5.0, deadline - time.monotonic())

    # Stufe 1: über "lms".
    lms = find_lms()
    if lms and _start(lms, port) and _wait_until_reachable(base_url, min(remaining(), 30.0)):
        return None

    # Stufe 2: LM Studio selbst öffnen. Nach der Installation fehlt "lms" im
    # Profil, bis LM Studio einmal lief; manchmal braucht "lms" auch das
    # laufende Programm.
    app = find_app()
    if not app:
        # "lms.exe" im Profil bleibt nach einer Deinstallation liegen und läuft ohne
        # das Programm nicht – ohne das Programm ist LM Studio nicht installiert.
        return "LM Studio ist auf diesem Rechner nicht installiert."
    if not _launch_app(app):
        return "LM Studio konnte nicht geöffnet werden."

    # Erst warten, bis das Programm oben ist, dann den Server starten; ein
    # zweiter Versuch, falls LM Studio länger zum Hochfahren brauchte.
    retry_after = [_AFTER_LAUNCH_FIRST, _AFTER_LAUNCH_SECOND]
    started_at = time.monotonic()
    while time.monotonic() < deadline:
        if is_reachable(base_url):
            return None
        if retry_after and time.monotonic() - started_at >= retry_after[0]:
            retry_after.pop(0)
            lms = find_lms()
            if lms:
                _start(lms, port)
            continue
        time.sleep(1.0)
    return (f"LM Studio wurde geöffnet, der Server antwortet aber nicht auf Port {port}. "
            f"In LM Studio unter „Developer“ den Server einschalten.")


def _start(lms: str, port: int) -> bool:
    """``lms server start``. True nur, wenn das Programm ohne Fehler endete."""
    code, _ = run_lms(lms, "server", "start", "--port", str(port), timeout=120)
    return code == 0


def _launch_app(app: str) -> bool:
    """Öffnet LM Studio losgelöst von Blitzdiktat und möglichst im Hintergrund."""
    try:
        flags = 0
        startup = None
        if os.name == "nt":
            flags = (getattr(subprocess, "DETACHED_PROCESS", 0)
                     | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
            startup = subprocess.STARTUPINFO()
            startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startup.wShowWindow = 7        # SW_SHOWMINNOACTIVE: minimiert, ohne Fokus
        subprocess.Popen(
            [app], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=flags, startupinfo=startup, close_fds=True,
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


def run_lms(lms: str, *args: str, timeout: float = 120) -> tuple[int, str]:
    """Führt "lms" still aus. Rückgabe: (Exit-Code, Ausgabe); -1 bei Start-/Zeitfehler."""
    try:
        done = subprocess.run(
            [lms, *args], stdin=subprocess.DEVNULL, capture_output=True,
            timeout=timeout, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        out = (done.stdout or b"").decode("utf-8", "replace") + (done.stderr or b"").decode("utf-8", "replace")
        return done.returncode, out
    except (OSError, subprocess.SubprocessError):
        return -1, ""


# ── Modell laden ────────────────────────────────────────────────────────────

def _norm(name: str) -> str:
    return (name or "").strip().lower().split("/")[-1]


def loaded_models(lms: str) -> list[str] | None:
    """Namen der geladenen Modelle (``lms ps --json``); None, wenn nicht ermittelbar."""
    code, out = run_lms(lms, "ps", "--json", timeout=30)
    if code != 0:
        return None
    try:
        data = json.loads(out[out.find("["):] if "[" in out else out)
    except ValueError:
        return None
    names: list[str] = []

    def collect(item) -> None:
        if isinstance(item, dict):
            for key in ("identifier", "modelKey", "path"):
                if isinstance(item.get(key), str):
                    names.append(item[key])
        elif isinstance(item, list):
            for sub in item:
                collect(sub)

    collect(data)
    return names


def ensure_model_loaded(base_url: str, model: str) -> bool:
    """Lädt das Modell mit ausreichender Kontextlänge, falls es nicht geladen ist.

    Bestmöglich: Läuft etwas nicht, bleibt es beim automatischen Laden von LM
    Studio (JIT). True = Modell ist geladen oder konnte geladen werden.
    """
    if not model or not is_local_url(base_url):
        return False
    key = _norm(model)
    if key in _loaded_ok:
        return True
    lms = find_lms()
    if not lms:
        return False
    names = loaded_models(lms)
    if names is not None and any(_norm(n) == key for n in names):
        _loaded_ok.add(key)
        return True
    code, _ = run_lms(lms, "load", model, "-c", str(CONTEXT_LENGTH), "-y", timeout=300)
    if code == 0:
        _loaded_ok.add(key)
        return True
    return False


def forget_loaded() -> None:
    """Merkt sich nicht mehr, welche Modelle geladen sind (z. B. nach einem Neustart des Servers)."""
    _loaded_ok.clear()
