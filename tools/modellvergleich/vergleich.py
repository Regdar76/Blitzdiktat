# Copyright (c) 2026 Thorben Meier. MIT License.
"""Modellvergleich für die lokale KI.

Schickt die echten Blitzdiktat-Prompts mit deutschen Beispiel-Diktaten an ein
Modell im lokalen LM-Studio-Server und misst Ladezeit, Zeit bis zum ersten
Zeichen und Tempo. Ergebnis: eine JSON-Datei je Lauf unter ergebnisse/.

Aufruf:  python vergleich.py <modell-key> [--gpu off|max] [--ctx 8192]
"""

import argparse
import ctypes
import json
import os
import subprocess
import sys
import time
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "BlitzdiktatWin"))

from openai import OpenAI  # noqa: E402

from services import llm_service  # noqa: E402
from features.workflows.dampf_ablassen_workflow import DEFAULT_SYSTEM_PROMPT as DAMPF_PROMPT  # noqa: E402
from features.workflows.protokoll_workflow import PROTOKOLL_SYSTEM_PROMPT  # noqa: E402

import proben  # noqa: E402

BASE_URL = "http://localhost:1234/v1"
IDENT = "bench"


class _MemStatus(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def ram_frei_gb() -> float:
    st = _MemStatus()
    st.dwLength = ctypes.sizeof(st)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st))
    return st.ullAvailPhys / 1024 ** 3


def vram_belegt_mb() -> int | None:
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10,
        ).stdout.strip()
        return int(out.splitlines()[0])
    except Exception:
        return None


def lms(*args: str, timeout: int = 900) -> subprocess.CompletedProcess:
    return subprocess.run(["lms", *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)


def aufgaben() -> list[dict]:
    settings = SimpleNamespace(
        system_prompt="", tone="neutral", context="E-Mail an eine Kundin",
        custom_terms=["Petersen", "I-Log"],
    )
    return [
        dict(id="verbessern", name="Blitzdiktat+",
             system=llm_service._build_improvement_prompt(settings),
             user=proben.VERBESSERN, temp=0.3),
        dict(id="dampf", name="Blitzdiktat $%&!",
             system=DAMPF_PROMPT, user=proben.DAMPF, temp=0.4),
        dict(id="emoji", name="Blitzdiktat :)",
             system=llm_service._build_emoji_prompt("mittel"),
             user=proben.EMOJI, temp=0.3),
        dict(id="protokoll", name="Protokoll",
             system=PROTOKOLL_SYSTEM_PROMPT,
             user=f"Aufnahmedatum: {proben.AUFNAHMEDATUM}\n\n{proben.PROTOKOLL}", temp=0.2),
        dict(id="vokabular", name="Vokabular-Extraktion",
             system=llm_service._EXTRACT_TERMS_PROMPT, user=proben.VOKABULAR, temp=0.0),
    ]


def pruefe(task_id: str, text: str) -> dict:
    regel = proben.PRUEFUNG[task_id]
    low = text.lower()
    fehlt = [g[0] for g in regel["muss"] if not any(w.lower() in low for w in g)]
    verboten = [w for w in regel["darf_nicht"] if w.lower() in low]
    res = {"fehlt": fehlt, "verboten": verboten,
           "treffer": f"{len(regel['muss']) - len(fehlt)}/{len(regel['muss'])}"}
    if task_id == "vokabular":
        try:
            res["json_ok"] = isinstance(json.loads(text), list)
        except Exception:
            res["json_ok"] = False
    return res


def frage(client: OpenAI, system: str, user: str, temp: float, extra: dict) -> dict:
    t0 = time.perf_counter()
    t_erstes = None
    teile: list[str] = []
    denk: list[str] = []
    usage = None
    stream = client.chat.completions.create(
        model=IDENT,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=temp, max_tokens=3000, stream=True,
        stream_options={"include_usage": True}, extra_body=extra or None,
    )
    for chunk in stream:
        if chunk.usage:
            usage = chunk.usage
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        r = getattr(delta, "reasoning_content", None) or (delta.model_extra or {}).get("reasoning")
        if r:
            denk.append(r)
        if delta.content:
            if t_erstes is None:
                t_erstes = time.perf_counter()
            teile.append(delta.content)
    t1 = time.perf_counter()
    text = "".join(teile).strip()
    out_tok = usage.completion_tokens if usage else None
    return {
        "text": text,
        "denk_zeichen": len("".join(denk)),
        "sek_gesamt": round(t1 - t0, 1),
        "sek_bis_erstes_zeichen": round((t_erstes or t1) - t0, 1),
        "tokens_ein": usage.prompt_tokens if usage else None,
        "tokens_aus": out_tok,
        "tokens_pro_sek": round(out_tok / (t1 - t0), 1) if out_tok else None,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("modell")
    ap.add_argument("--gpu", default="off")
    ap.add_argument("--ctx", default="8192")
    ap.add_argument("--kein-denken", action="store_true",
                    help="Denkmodus per Anfrage-Parameter abschalten (für Reasoning-Modelle)")
    ap.add_argument("--nur", default="", help="nur diese Aufgaben-IDs (Komma-getrennt)")
    args = ap.parse_args()

    lms("unload", "--all")
    time.sleep(2)
    ram_vor, vram_vor = ram_frei_gb(), vram_belegt_mb()

    t0 = time.perf_counter()
    res = lms("load", args.modell, "--gpu", args.gpu, "-c", args.ctx,
              "--identifier", IDENT, "-y")
    lade_sek = round(time.perf_counter() - t0, 1)
    if res.returncode != 0:
        print("LADEN FEHLGESCHLAGEN:\n", res.stdout[-1500:], res.stderr[-1500:])
        sys.exit(1)
    ram_nach, vram_nach = ram_frei_gb(), vram_belegt_mb()

    client = OpenAI(base_url=BASE_URL, api_key="lm-studio", timeout=1800)
    extra = {"reasoning_effort": "none"} if args.kein_denken else {}

    # Aufwärmen, damit die erste Messung nicht das Nachladen enthält.
    frage(client, "Antworte kurz.", "Sag Hallo.", 0.0, extra)

    nur = {x for x in args.nur.split(",") if x}
    laeufe = []
    for a in aufgaben():
        if nur and a["id"] not in nur:
            continue
        r = frage(client, a["system"], a["user"], a["temp"], extra)
        r.update(id=a["id"], name=a["name"], pruefung=pruefe(a["id"], r["text"]))
        laeufe.append(r)
        print(f"{a['name']:22} {r['sek_gesamt']:6.1f} s  erstes Zeichen {r['sek_bis_erstes_zeichen']:5.1f} s  "
              f"{r['tokens_pro_sek']} tok/s  Prüfwörter {r['pruefung']['treffer']}"
              f"{'  DENKT' if r['denk_zeichen'] else ''}", flush=True)

    lms("unload", "--all")

    ergebnis = {
        "modell": args.modell, "gpu": args.gpu, "ctx": int(args.ctx),
        "kein_denken": args.kein_denken, "lade_sek": lade_sek,
        "ram_belegt_gb": round(ram_vor - ram_nach, 1),
        "vram_belegt_mb": (vram_nach - vram_vor) if vram_vor is not None and vram_nach is not None else None,
        "laeufe": laeufe,
    }
    os.makedirs(os.path.join(HERE, "ergebnisse"), exist_ok=True)
    name = args.modell.replace("/", "_").replace("@", "_") + f"__gpu-{args.gpu}"
    if args.kein_denken:
        name += "__ohne-denken"
    pfad = os.path.join(HERE, "ergebnisse", name + ".json")
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump(ergebnis, f, ensure_ascii=False, indent=2)
    print(f"Laden {lade_sek} s, RAM {ergebnis['ram_belegt_gb']} GB, VRAM {ergebnis['vram_belegt_mb']} MB → {pfad}")


if __name__ == "__main__":
    main()
