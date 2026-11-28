# Copyright (c) 2026 Thorben Meier. MIT License.
"""
Geschwindigkeitstest und Download für die lokale KI (LM Studio).

* ``measure``: lädt ein Modell, lässt es ein kurzes deutsches Diktat
  überarbeiten und rechnet daraus hoch, wie lange ein Diktat und ein
  Protokoll auf diesem Rechner dauern.
* ``download``: lädt ein Modell aus dem Katalog über ``lms get`` herunter.

Beides läuft im Hintergrund-Thread der Einstellungen; ``progress`` bekommt
kurze Statustexte für die Anzeige.
"""

import time
from typing import Callable

from . import llm_service, local_server, prompts
from .model_catalog import LocalModel, Measurement, estimate_seconds, is_installed

Progress = Callable[[str], None]

TEST_IDENTIFIER = "blitzdiktat-speedtest"

# Typisches Diktat für $%&! – etwa 60 Wörter, so viel wie ein kurzes Diktat im Alltag.
_SAMPLE = (
    "Also das geht so echt nicht weiter. Jetzt hat der Lieferant schon wieder den Termin "
    "verschoben, das dritte Mal, und keiner sagt uns Bescheid. Wir hatten fest für Montag "
    "die Lieferung zugesagt, und jetzt heißt es, es dauert noch zwei Wochen. Ich möchte "
    "bis nächsten Mittwoch eine verbindliche Antwort, sonst können die den Auftrag vergessen."
)


def _lms() -> str:
    lms = local_server.find_lms()
    if not lms:
        raise RuntimeError("LM Studio ist nicht installiert.")
    return lms


def _ensure_server(base_url: str, progress: Progress) -> None:
    if local_server.is_reachable(base_url):
        return
    progress("Starte LM Studio …")
    result = local_server.start_local_server(base_url, force=True)
    if not result.ok:
        raise RuntimeError(result.reason or "Der lokale Server konnte nicht gestartet werden.")


def download(model: LocalModel, base_url: str, progress: Progress) -> tuple[bool, str]:
    """Lädt das Modell herunter. Rückgabe: (geschafft, Meldung)."""
    try:
        _ensure_server(base_url, progress)
        lms = _lms()
        progress(f"Lade {model.title} herunter ({model.disk_gb:.1f} GB) – das kann einige Minuten dauern …")
        code, out = local_server.run_lms(lms, "get", model.download, "--gguf", "-y", timeout=7200)
        if code != 0:
            tail = " ".join(out.split())[-160:]
            return False, f"Download fehlgeschlagen. {tail}".strip()
        names = llm_service.list_models(base_url, timeout=15)
        if not is_installed(model, names):
            return False, "Der Download ist durchgelaufen, das Modell erscheint aber nicht im Server."
        return True, f"{model.title} ist installiert."
    except Exception as e:
        return False, str(e)[:200]


def measure(model: LocalModel, base_url: str, api_key: str, progress: Progress) -> Measurement:
    """Misst Ladezeit und Tempo eines installierten Modells."""
    from openai import BadRequestError, OpenAI

    result = Measurement(model=model, ok=False)
    lms = None
    try:
        _ensure_server(base_url, progress)
        lms = _lms()
        progress(f"{model.title}: lade das Modell …")
        # Frischer Zustand: sonst verfälscht ein bereits geladenes Modell Speicher und Tempo.
        local_server.run_lms(lms, "unload", "--all", timeout=60)
        local_server.forget_loaded()
        t0 = time.perf_counter()
        code, out = local_server.run_lms(
            lms, "load", model.key, "--identifier", TEST_IDENTIFIER,
            "-c", str(local_server.CONTEXT_LENGTH), "-y", timeout=600,
        )
        result.load_s = time.perf_counter() - t0
        if code != 0:
            tail = " ".join(out.split())[-160:]
            result.error = f"Modell ließ sich nicht laden. {tail}".strip()
            return result

        client = OpenAI(base_url=base_url, api_key=api_key or "nicht-noetig", timeout=600, max_retries=0)
        extra = {"reasoning_effort": "none"}

        def ask(system: str, user: str, max_tokens: int):
            kwargs = dict(
                model=TEST_IDENTIFIER, temperature=0.2, max_tokens=max_tokens, stream=True,
                stream_options={"include_usage": True},
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            )
            try:
                stream = client.chat.completions.create(**kwargs, extra_body=extra)
            except BadRequestError:
                stream = client.chat.completions.create(**kwargs)
            started = time.perf_counter()
            first = None
            usage = None
            for chunk in stream:
                if chunk.usage:
                    usage = chunk.usage
                if chunk.choices and chunk.choices[0].delta.content and first is None:
                    first = time.perf_counter()
            return started, first or time.perf_counter(), time.perf_counter(), usage

        progress(f"{model.title}: Aufwärmen …")
        ask("Antworte kurz.", "Sag Hallo.", 8)

        progress(f"{model.title}: messe das Tempo …")
        started, first, end, usage = ask(
            prompts.DAMPF_LOCAL_SYSTEM_PROMPT, prompts.dampf_local_user(_SAMPLE), 400,
        )
        out_tokens = getattr(usage, "completion_tokens", None) or 0
        in_tokens = getattr(usage, "prompt_tokens", None) or 0
        if not out_tokens or end - first < 0.05:
            result.error = "Das Modell lieferte keine auswertbare Antwort."
            return result
        result.tps = out_tokens / (end - first)
        prefill_tps = in_tokens / (first - started) if in_tokens and first - started > 0.05 else None
        result.dictation_s = end - started
        result.protocol_s = estimate_seconds(result.tps, prefill_tps)[1]
        result.ok = True
        return result
    except Exception as e:
        result.error = str(e)[:200]
        return result
    finally:
        if lms:
            local_server.run_lms(lms, "unload", TEST_IDENTIFIER, timeout=60)
        local_server.forget_loaded()
