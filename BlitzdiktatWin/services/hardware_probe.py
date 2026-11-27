# Copyright (c) 2026 Thorben Meier. MIT License.
"""
Erkennt, was dieser Rechner für eine lokale KI mitbringt: Arbeitsspeicher,
Prozessor und Grafikkarte samt Grafikspeicher.

Der Grafikspeicher lässt sich unter Windows nicht zuverlässig über WMI lesen
(Win32_VideoController meldet höchstens 4 GB), deshalb der Reihe nach:
  1. nvidia-smi (NVIDIA-Treiber),
  2. "lms runtime survey" (LM Studio, kennt auch AMD/Intel),
  3. die Registry (HardwareInformation.qwMemorySize, 64 Bit).
"""

import ctypes
import os
import re
import subprocess
from dataclasses import dataclass, field

_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


@dataclass
class Gpu:
    name: str
    vram_gb: float | None = None       # None = Größe unbekannt

    def describe(self) -> str:
        return f"{self.name} ({self.vram_gb:.0f} GB)" if self.vram_gb else self.name


@dataclass
class Hardware:
    ram_gb: float = 0.0
    cpu_threads: int = 0
    gpus: list[Gpu] = field(default_factory=list)

    @property
    def best_vram_gb(self) -> float:
        """Grafikspeicher der größten Grafikkarte (0, wenn keine oder unbekannt)."""
        return max((g.vram_gb or 0.0 for g in self.gpus), default=0.0)

    def describe(self) -> str:
        gpu = ", ".join(g.describe() for g in self.gpus) if self.gpus else "keine Grafikkarte erkannt"
        return f"{self.ram_gb:.0f} GB Arbeitsspeicher · {self.cpu_threads} Prozessor-Threads · {gpu}"


# ── Auswertung der Programmausgaben (rein, gut testbar) ─────────────────────

def parse_nvidia_smi(output: str) -> list[Gpu]:
    """Zeilen wie "NVIDIA GeForce RTX 2080 Ti, 11264" (Name, MiB)."""
    gpus: list[Gpu] = []
    for line in output.splitlines():
        name, _, mib = line.rpartition(",")
        name = name.strip()
        mib = mib.strip()
        if name and mib.isdigit():
            gpus.append(Gpu(name, int(mib) / 1024))
    return gpus


_SURVEY_GPU = re.compile(r"^(?P<name>.+?)\s+\((?P<kind>[^)]*)\)\s+(?P<size>[\d.,]+)\s*(?P<unit>GiB|MiB|GB|MB)\s*$")


def parse_lms_survey(output: str) -> list[Gpu]:
    """Zeilen wie "NVIDIA GeForce RTX 2080 Ti (CUDA, Discrete)   11.00 GiB"."""
    gpus: list[Gpu] = []
    for line in output.splitlines():
        m = _SURVEY_GPU.match(line.strip())
        if not m:
            continue
        size = float(m.group("size").replace(",", "."))
        if m.group("unit") in ("MiB", "MB"):
            size /= 1024
        gpus.append(Gpu(m.group("name").strip(), size))
    return gpus


# ── Messung ─────────────────────────────────────────────────────────────────

class _MemStatus(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def ram_gb() -> float:
    try:
        st = _MemStatus()
        st.dwLength = ctypes.sizeof(st)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st))
        return st.ullTotalPhys / 1024 ** 3
    except Exception:
        return 0.0


def _run(args: list[str], timeout: float = 20) -> str:
    try:
        done = subprocess.run(
            args, stdin=subprocess.DEVNULL, capture_output=True, timeout=timeout,
            creationflags=_NO_WINDOW,
        )
        if done.returncode == 0:
            return done.stdout.decode("utf-8", "replace")
    except (OSError, subprocess.SubprocessError):
        pass
    return ""


def _gpus_from_nvidia_smi() -> list[Gpu]:
    return parse_nvidia_smi(_run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"]))


def _gpus_from_lms() -> list[Gpu]:
    from . import local_server
    lms = local_server.find_lms()
    if not lms:
        return []
    return parse_lms_survey(_run([lms, "runtime", "survey"], timeout=60))


def _gpus_from_registry() -> list[Gpu]:
    gpus: list[Gpu] = []
    try:
        import winreg
        key_path = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as root:
            i = 0
            while True:
                try:
                    sub = winreg.EnumKey(root, i)
                except OSError:
                    break
                i += 1
                try:
                    with winreg.OpenKey(root, sub) as k:
                        name = str(winreg.QueryValueEx(k, "DriverDesc")[0])
                        raw = winreg.QueryValueEx(k, "HardwareInformation.qwMemorySize")[0]
                except OSError:
                    continue
                size = int.from_bytes(raw, "little") if isinstance(raw, (bytes, bytearray)) else int(raw)
                if size > 0:
                    gpus.append(Gpu(name, size / 1024 ** 3))
    except Exception:
        return []
    return gpus


def detect() -> Hardware:
    """Misst den Rechner. Dauert wenige Sekunden."""
    gpus = _gpus_from_nvidia_smi() or _gpus_from_lms() or _gpus_from_registry()
    return Hardware(ram_gb=ram_gb(), cpu_threads=os.cpu_count() or 0, gpus=gpus)
