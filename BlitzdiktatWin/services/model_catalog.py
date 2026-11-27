# Copyright (c) 2026 Thorben Meier. MIT License.
"""
Welche lokalen Sprachmodelle Blitzdiktat anbietet und welches zu welchem Rechner passt.

Die Zahlen stammen aus dem Modellvergleich (tools/modellvergleich, Berichte
unter ergebnisse/): Prüfwörter-Treffer mit den echten Blitzdiktat-Prompts und
Tempo auf dem Prozessor. Sie sind Richtwerte – der Geschwindigkeitstest in den
Einstellungen misst auf dem echten Rechner nach und hat das letzte Wort.
"""

from dataclasses import dataclass

from .hardware_probe import Hardware

# Arbeitsspeicher, den Windows, Whisper und die übrigen Programme brauchen.
RAM_RESERVE_GB = 6.0


@dataclass(frozen=True)
class LocalModel:
    key: str            # Name, unter dem der Server das Modell anbietet (lms ls)
    title: str
    download: str       # Name für "lms get"
    disk_gb: float      # Platz auf der Festplatte (Modell, ohne Bild-Anhang)
    ram_gb: float       # Arbeitsspeicher auf dem Prozessor (Kontext 8192)
    vram_gb: float      # Grafikspeicher bei voller Auslagerung (mit Reserve)
    quality: int        # 1–5, nach Prüfwörtern im Modellvergleich
    cpu_tps: float      # Tokens pro Sekunde auf dem Prozessor (Referenzrechner)
    note: str
    aliases: tuple[str, ...] = ()   # andere Namen desselben Modells im Server


CATALOG: tuple[LocalModel, ...] = (
    LocalModel(
        key="google/gemma-4-e2b", title="Gemma 4 E2B", download="google/gemma-4-e2b",
        aliases=("gemma-4-e2b-it",),     # so heißt die Datei, die der Installer ablegt
        disk_gb=3.4, ram_gb=3.7, vram_gb=4.5, quality=3, cpu_tps=11.7,
        note="Standard. Klein und schnell, Ergebnis gut mit den lokalen Prompts.",
    ),
    LocalModel(
        key="google/gemma-4-e4b", title="Gemma 4 E4B", download="google/gemma-4-e4b",
        aliases=("gemma-4-e4b-it",),
        disk_gb=5.0, ram_gb=5.4, vram_gb=6.5, quality=4, cpu_tps=6.8,
        note="Genauer bei Blitzdiktat+ und Protokoll; auf dem Prozessor langsam, mit Grafikkarte flott.",
    ),
    LocalModel(
        key="qwen/qwen3.5-9b", title="Qwen 3.5 9B", download="qwen/qwen3.5-9b",
        disk_gb=6.6, ram_gb=6.2, vram_gb=12.0, quality=5, cpu_tps=4.9,
        note="Beste Qualität im Vergleich, aber nur mit starker Grafikkarte (ab ca. 12 GB) alltagstauglich.",
    ),
)


def normalize(name: str) -> str:
    """'qwen/Qwen3.5-9B' → 'qwen3.5-9b' (Herausgeber und Schreibweise ignorieren)."""
    return (name or "").strip().lower().split("/")[-1]


def _names(model: LocalModel) -> set[str]:
    return {normalize(model.key), *(normalize(a) for a in model.aliases)}


def by_key(key: str) -> LocalModel | None:
    wanted = normalize(key)
    return next((m for m in CATALOG if wanted in _names(m)), None)


def server_name(model: LocalModel, server_models: list[str]) -> str | None:
    """Wie der Server dieses Modell nennt (None = nicht installiert)."""
    names = _names(model)
    return next((n for n in server_models if normalize(n) in names), None)


def is_installed(model: LocalModel, server_models: list[str]) -> bool:
    return server_name(model, server_models) is not None


def resolve_model(configured: str, server_models: list[str]) -> str | None:
    """Gespeicherter Modellname, den der Server so nicht mehr kennt → sein heutiger Name.

    LM Studio vergibt Namen neu (z. B. "gemma-4-e2b-it" → "google/gemma-4-e2b"),
    wenn ein Modell über seinen Katalog geladen wird. None = nichts zu ändern
    (Name stimmt bereits oder das Modell ist nicht installiert).
    """
    if not configured or configured in server_models:
        return None
    model = by_key(configured)
    return server_name(model, server_models) if model else None


# ── Einschätzung nach Hardware ──────────────────────────────────────────────

@dataclass
class Rating:
    model: LocalModel
    fits: bool              # läuft auf diesem Rechner überhaupt
    on_gpu: bool            # passt vollständig in den Grafikspeicher
    est_tps: float          # geschätzte Tokens pro Sekunde
    est_dictation_s: float
    est_protocol_s: float
    reason: str             # warum es nicht passt (leer, wenn es passt)


# Grobe Mengen für die Schätzung: ein Diktat (kurzer Text raus), ein Protokoll
# (langer Text rein und raus).
_DICTATION_PROMPT_TOK, _DICTATION_OUT_TOK = 450, 130
_PROTOCOL_PROMPT_TOK, _PROTOCOL_OUT_TOK = 1900, 650
# Gemessen: Gemma 4 E2B schafft auf einer RTX 2080 Ti 128 Tokens/s, auf dem Prozessor
# 12 – Faktor 11. Vorsichtig angesetzt, weil Karten und Treiber stark schwanken.
_GPU_SPEEDUP = 5.0


def estimate_seconds(tps: float, prefill_tps: float | None = None) -> tuple[float, float]:
    """(Diktat, Protokoll) in Sekunden aus Erzeugungstempo und optional Einlesetempo."""
    if tps <= 0:
        return float("inf"), float("inf")
    prefill = prefill_tps or tps * 12      # Einlesen geht deutlich schneller als Schreiben
    dictation = _DICTATION_PROMPT_TOK / prefill + _DICTATION_OUT_TOK / tps
    protocol = _PROTOCOL_PROMPT_TOK / prefill + _PROTOCOL_OUT_TOK / tps
    return dictation, protocol


def rate(hw: Hardware, model: LocalModel) -> Rating:
    on_gpu = hw.best_vram_gb >= model.vram_gb
    ram_ok = hw.ram_gb >= model.ram_gb + RAM_RESERVE_GB
    if on_gpu:
        tps = model.cpu_tps * _GPU_SPEEDUP
    else:
        # Mehr Prozessor-Threads → schneller; Referenzrechner hat etwa 16.
        factor = min(1.5, max(0.4, (hw.cpu_threads or 8) / 16))
        tps = model.cpu_tps * factor
    dictation, protocol = estimate_seconds(tps)
    reason = ""
    if not on_gpu and not ram_ok:
        reason = (f"braucht ca. {model.ram_gb + RAM_RESERVE_GB:.0f} GB Arbeitsspeicher "
                  f"(vorhanden: {hw.ram_gb:.0f} GB)")
    return Rating(model, fits=(on_gpu or ram_ok), on_gpu=on_gpu, est_tps=tps,
                  est_dictation_s=dictation, est_protocol_s=protocol, reason=reason)


# Was noch als alltagstauglich gilt.
MAX_DICTATION_S = 25.0
MAX_PROTOCOL_S = 150.0


def recommend(hw: Hardware) -> tuple[LocalModel | None, list[Rating]]:
    """Das beste Modell, das auf diesem Rechner noch flott genug läuft (None = keines)."""
    ratings = [rate(hw, m) for m in CATALOG]
    return _best([(r.model, r.fits, r.est_dictation_s, r.est_protocol_s) for r in ratings]), ratings


def _best(rows: list[tuple[LocalModel, bool, float, float]]) -> LocalModel | None:
    ok = [(m, d, p) for m, fits, d, p in rows if fits]
    if not ok:
        return None
    good = [(m, d, p) for m, d, p in ok if d <= MAX_DICTATION_S and p <= MAX_PROTOCOL_S]
    if good:
        return max(good, key=lambda x: (x[0].quality, -x[2]))[0]
    return min(ok, key=lambda x: x[2])[0]         # nichts ist flott: das schnellste


@dataclass
class Measurement:
    model: LocalModel
    ok: bool
    error: str = ""
    load_s: float = 0.0
    tps: float = 0.0
    dictation_s: float = 0.0
    protocol_s: float = 0.0


def pick_best(results: list[Measurement]) -> LocalModel | None:
    """Wie recommend, aber aus echten Messungen."""
    rows = [(r.model, r.ok, r.dictation_s, r.protocol_s) for r in results]
    return _best(rows)


def speed_label(protocol_s: float) -> str:
    if protocol_s <= 45:
        return "schnell"
    if protocol_s <= MAX_PROTOCOL_S:
        return "mittel"
    return "langsam"


def format_duration(seconds: float) -> str:
    if seconds == float("inf"):
        return "?"
    if seconds < 90:
        return f"{seconds:.0f} s"
    return f"{seconds / 60:.1f} min".replace(".", ",")


def choose(hw: Hardware, server_models: list[str]) -> tuple[LocalModel | None, LocalModel | None]:
    """(Zielmodell, Zwischenlösung) für die automatische Einrichtung.

    Ziel ist das für diesen Rechner empfohlene Modell. Fehlt es noch, bleibt als
    Zwischenlösung das beste bereits installierte Modell, das auf dem Rechner läuft
    (None, wenn keines installiert ist oder das Ziel schon da ist).
    """
    target, ratings = recommend(hw)
    if target is None or is_installed(target, server_models):
        return target, None
    installed = [(r.model, r.fits, r.est_dictation_s, r.est_protocol_s)
                 for r in ratings if is_installed(r.model, server_models)]
    return target, _best(installed)
