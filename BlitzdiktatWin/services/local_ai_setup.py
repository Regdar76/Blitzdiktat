# Copyright (c) 2026 Thorben Meier. MIT License.
"""
Automatische Einrichtung der lokalen KI – der Anwender muss nichts tun.

Beim Start prüft Blitzdiktat, ob die lokale Text-KI (LM Studio mit einem
Sprachmodell) bereit ist, und holt nach, was fehlt:

  1. LM Studio fehlt          → pinned Installer laden, Prüfsumme prüfen, still installieren.
  2. Server läuft nicht       → starten (siehe local_server).
  3. Hardware prüfen          → bestes Modell wählen, das auf diesem Rechner flott läuft.
  4. Modell fehlt             → herunterladen. Bis dahin arbeitet ein schon installiertes
                                Modell weiter; danach wird umgeschaltet.
  5. Modell laden             → mit ausreichender Kontextlänge.

Eine manuelle Wahl des Nutzers (Erweitert) schaltet die Automatik aus
(``settings.local_ai_auto``). Läuft die KI nicht auf diesem Rechner oder hat der
Nutzer einen OpenAI-Schlüssel und nichts anderes gewählt, passiert nichts.
"""

import hashlib
import json
import os
import subprocess
import tempfile
import threading
import time
import urllib.request
from dataclasses import dataclass
from typing import Callable

from . import (
    credentials_service, hardware_probe, llm_service, local_benchmark, local_server, model_catalog,
)
from .local_ai_pins import LM_STUDIO_BYTES, LM_STUDIO_SHA256, LM_STUDIO_URL

IDLE, WORKING, READY, FAILED, NOT_NEEDED = "idle", "working", "ready", "failed", "not_needed"

OWNERSHIP_FILE = "lokale_ki_installiert.json"
_EXTRA_FREE_GB = 3.0          # Reserve neben dem Modell (Bildanhang, Zwischendateien)
_LM_STUDIO_FREE_GB = 4.0


class SetupError(Exception):
    """Einrichtung gescheitert; der Text ist für den Anwender gedacht."""


@dataclass
class Status:
    state: str = IDLE
    message: str = ""
    progress: float | None = None        # 0..1, wenn bekannt (Downloads), sonst None


status = Status()
_listeners: list[Callable[[Status], None]] = []
_run_lock = threading.Lock()


def subscribe(callback: Callable[[Status], None]) -> None:
    _listeners.append(callback)


def _set(state: str, message: str = "", progress: float | None = None) -> None:
    status.state, status.message, status.progress = state, message, progress
    for cb in list(_listeners):
        try:
            cb(status)
        except Exception:
            pass


def is_working() -> bool:
    return status.state == WORKING


def mark_starting() -> None:
    """Sofort als "in Arbeit" melden, noch bevor der Hintergrund-Thread läuft –
    sonst wäre die App in den ersten Augenblicken schon bedienbar."""
    _set(WORKING, "Lokale KI wird geprüft …")


# ── Wann ist die Einrichtung nötig? ─────────────────────────────────────────

def _appdata_dir() -> str:
    base = os.environ.get("APPDATA", os.path.expanduser("~"))
    return os.path.join(base, "Blitzdiktat")


def ownership_path() -> str:
    return os.path.join(_appdata_dir(), OWNERSHIP_FILE)


def installer_wanted_local_ai() -> bool:
    """Das Setup hat die lokale KI vorgesehen (Merkdatei vorhanden)."""
    return os.path.exists(ownership_path())


def needs_local_ai(settings) -> bool:
    if not getattr(settings, "local_ai_auto", True):
        return False
    url = llm_service.normalize_base_url(settings.custom_llm_base_url) or llm_service.DEFAULT_CUSTOM_BASE_URL
    if not local_server.is_local_url(url):
        return False
    if settings.llm_provider == llm_service.PROVIDER_CUSTOM:
        return True
    # Online-Anbieter ohne Schlüssel: nur wenn das Setup die lokale KI vorgesehen hat.
    return not (credentials_service.load_api_key() or "").strip() and installer_wanted_local_ai()


# ── Merkdatei (die Deinstallation entfernt, was Blitzdiktat installiert hat) ─

def remember_ownership(lmstudio: bool | None = None, gemma: bool | None = None) -> None:
    """Gleicher Aufbau wie im Setup: {"lmstudio": true, "gemma": false}; "true" bleibt erhalten."""
    flags = {"lmstudio": False, "gemma": False}
    try:
        with open(ownership_path(), "r", encoding="utf-8-sig") as f:
            flags.update({k: bool(v) for k, v in json.load(f).items() if k in flags})
    except (OSError, ValueError):
        pass
    if lmstudio:
        flags["lmstudio"] = True
    if gemma:
        flags["gemma"] = True
    os.makedirs(_appdata_dir(), exist_ok=True)
    text = '{"lmstudio": %s, "gemma": %s}' % (str(flags["lmstudio"]).lower(), str(flags["gemma"]).lower())
    with open(ownership_path(), "w", encoding="utf-8") as f:
        f.write(text)


# ── LM Studio installieren ──────────────────────────────────────────────────

def _free_gb(path: str) -> float:
    import shutil
    probe = path
    while probe and not os.path.exists(probe):
        probe = os.path.dirname(probe)
    return shutil.disk_usage(probe or os.path.expanduser("~")).free / 1024 ** 3


def _download_file(url: str, dest: str, sha256: str, size: int, progress: Callable[..., None]) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "Blitzdiktat"})
    digest = hashlib.sha256()
    done = 0
    last = 0.0
    try:
        with urllib.request.urlopen(request, timeout=60) as response, open(dest, "wb") as out:
            while True:
                chunk = response.read(1024 * 256)
                if not chunk:
                    break
                out.write(chunk)
                digest.update(chunk)
                done += len(chunk)
                if time.monotonic() - last > 1.0:
                    last = time.monotonic()
                    progress(
                        f"Lade LM Studio … {done / 1024 ** 2:.0f} von {size / 1024 ** 2:.0f} MB",
                        min(1.0, done / size) if size else None,
                    )
    except OSError as e:
        raise SetupError(f"LM Studio konnte nicht geladen werden (keine Internetverbindung?): {e}") from e
    if digest.hexdigest().lower() != sha256.lower():
        try:
            os.remove(dest)
        except OSError:
            pass
        raise SetupError("Der Download von LM Studio ist beschädigt (Prüfsumme stimmt nicht).")


def _desktop_shortcuts() -> list[str]:
    home = os.environ.get("USERPROFILE", os.path.expanduser("~"))
    folders = [os.path.join(home, "Desktop")]
    one = os.environ.get("OneDrive")
    if one:
        folders.append(os.path.join(one, "Desktop"))
    return [os.path.join(f, "LM Studio.lnk") for f in folders]


def install_lm_studio(progress: Callable[..., None]) -> None:
    """Lädt LM Studio (feste Version, Prüfsumme) und installiert es still."""
    if _free_gb(os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))) < _LM_STUDIO_FREE_GB:
        raise SetupError("Zu wenig freier Speicherplatz für LM Studio.")
    setup = os.path.join(tempfile.gettempdir(), "Blitzdiktat-LM-Studio-Setup.exe")
    _download_file(LM_STUDIO_URL, setup, LM_STUDIO_SHA256, LM_STUDIO_BYTES, progress)
    progress("Installiere LM Studio …")
    try:
        subprocess.run(
            [setup, "/S"], stdin=subprocess.DEVNULL, capture_output=True, timeout=900,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.SubprocessError) as e:
        raise SetupError(f"LM Studio ließ sich nicht installieren: {e}") from e
    finally:
        try:
            os.remove(setup)
        except OSError:
            pass
    deadline = time.monotonic() + 60
    while not local_server.find_app():
        if time.monotonic() > deadline:
            raise SetupError("LM Studio ließ sich nicht installieren.")
        time.sleep(1.0)
    remember_ownership(lmstudio=True)          # die Deinstallation räumt es wieder auf
    for lnk in _desktop_shortcuts():
        try:
            os.remove(lnk)
        except OSError:
            pass


# ── Modell herunterladen (mit Fortschritt) ──────────────────────────────────

def _models_dir() -> str:
    return os.path.join(os.path.expanduser("~"), ".lmstudio", "models")


def _partial_bytes() -> int:
    total = 0
    for root, _dirs, files in os.walk(_models_dir()):
        for name in files:
            if name.startswith("downloading_") or name.endswith(".part"):
                try:
                    total += os.path.getsize(os.path.join(root, name))
                except OSError:
                    pass
    return total


def _download_model(model: model_catalog.LocalModel, url: str, progress: Callable[..., None]) -> tuple[bool, str]:
    result: dict = {}

    def work() -> None:
        result["value"] = local_benchmark.download(model, url, lambda _text: None)

    thread = threading.Thread(target=work, daemon=True)
    thread.start()
    while thread.is_alive():
        thread.join(2.0)
        got = _partial_bytes() / 1024 ** 3
        total = model.disk_gb + 1                # Modell plus Bildanhang
        progress(f"Lade {model.title} … {got:.1f} von ca. {total:.1f} GB".replace(".", ","), min(0.99, got / total))
    return result.get("value", (False, "Download abgebrochen."))


# ── Ablauf ──────────────────────────────────────────────────────────────────

def run(
    settings,
    save: Callable[[], None],
    notify: Callable[[str], None] | None = None,
    force: bool = False,
) -> None:
    """Richtet die lokale KI ein (blockiert; im Hintergrund-Thread aufrufen).

    force=True: auch ausführen, wenn die Automatik aus ist (Knopf in den Einstellungen).
    """
    if not _run_lock.acquire(blocking=False):
        return
    try:
        if force:
            settings.local_ai_auto = True
        if not needs_local_ai(settings):
            _set(NOT_NEEDED, "")
            return
        try:
            _run(settings, save, notify)
        except SetupError as e:
            _set(FAILED, str(e))
            if notify:
                notify(f"Lokale KI konnte nicht eingerichtet werden: {e}")
        except Exception as e:                                # nie die App stören
            _set(FAILED, f"Unerwarteter Fehler: {str(e)[:120]}")
    finally:
        _run_lock.release()


def _activate(settings, save, server_name: str) -> None:
    if settings.llm_provider == llm_service.PROVIDER_CUSTOM and settings.custom_llm_model == server_name:
        return
    settings.llm_provider = llm_service.PROVIDER_CUSTOM
    settings.custom_llm_model = server_name
    save()


def _run(settings, save, notify) -> None:
    url = llm_service.normalize_base_url(settings.custom_llm_base_url) or llm_service.DEFAULT_CUSTOM_BASE_URL
    key = credentials_service.load_custom_api_key() or ""
    did_work = False
    _set(WORKING, "Lokale KI wird geprüft …")

    # Maßgeblich ist das Programm selbst: "lms.exe" im Profil bleibt nach einer
    # Deinstallation liegen und läuft ohne das Programm nicht.
    if not local_server.find_app():
        _set(WORKING, "Lade LM Studio …")
        install_lm_studio(lambda text, fraction=None: _set(WORKING, text, fraction))
        did_work = True

    _set(WORKING, "Starte die lokale KI …")
    started = local_server.start_local_server(url, force=True)
    if not started.ok:
        raise SetupError(started.reason or "Der lokale Server ließ sich nicht starten.")

    names = llm_service.list_models(url, key, timeout=15)
    configured = settings.custom_llm_model
    if configured and not model_catalog.by_key(configured) and configured in names:
        # Ein eigenes Modell des Nutzers (nicht aus unserem Katalog): nicht anfassen.
        local_server.ensure_model_loaded(url, configured)
        _set(READY, f"Lokale KI bereit: {configured}")
        return

    _set(WORKING, "Prüfe die Hardware …")
    hw = hardware_probe.detect()
    target, interim = model_catalog.choose(hw, names)
    if target is None:
        _handle_too_weak(settings, save, names, hw)
        return

    if interim is not None:                      # bis das Ziel da ist, damit arbeiten
        _activate(settings, save, model_catalog.server_name(interim, names))
        local_server.ensure_model_loaded(url, settings.custom_llm_model)

    if not model_catalog.is_installed(target, names):
        if _free_gb(os.path.expanduser("~")) < target.disk_gb + _EXTRA_FREE_GB:
            if interim is None:
                raise SetupError(f"Zu wenig freier Speicherplatz für {target.title}.")
            _set(READY, f"Lokale KI bereit: {interim.title} (für {target.title} fehlt Speicherplatz)")
            return
        ok, message = _download_model(target, url, lambda text, fraction=None: _set(WORKING, text, fraction))
        if not ok:
            if interim is None:
                raise SetupError(message)
            _set(READY, f"Lokale KI bereit: {interim.title} (Download von {target.title} gescheitert)")
            return
        did_work = True
        names = llm_service.list_models(url, key, timeout=15)

    server_name = model_catalog.server_name(target, names) or target.key
    _activate(settings, save, server_name)
    _set(WORKING, f"Lade {target.title} …")
    local_server.ensure_model_loaded(url, server_name)
    _set(READY, f"Lokale KI bereit: {target.title}")
    if did_work and notify:
        notify(f"Lokale KI ist bereit: {target.title}")


def _handle_too_weak(settings, save, names: list[str], hw) -> None:
    installed = [m for m in model_catalog.CATALOG if model_catalog.is_installed(m, names)]
    if installed:
        _activate(settings, save, model_catalog.server_name(installed[0], names))
        _set(READY, f"Lokale KI bereit: {installed[0].title} (der Rechner ist dafür knapp ausgestattet)")
        return
    raise SetupError(
        f"Dieser Rechner ({hw.describe()}) ist für eine lokale KI zu schwach. "
        "Bitte in den Einstellungen einen OpenAI-Schlüssel eintragen."
    )
