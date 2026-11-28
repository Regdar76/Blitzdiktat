# Copyright (c) 2026 Thorben Meier. MIT License.
"""Runde 2: $%&! und Protokoll mit mehreren Proben, App-Prompt gegen lokale Fassung.

Eingabe sind die Whisper-Transkripte aus transkripte.json (siehe sprechen.py).
Variante "standard" = Prompt und Aufbau wie heute in der App.
Variante "lokal"    = prompts_lokal.py (kurze Regeln, Kalender, Nachbearbeitung).

Aufruf:  python runde2.py <modell-key> [--gpu off|max] [--variante standard|lokal|beide]
                          [--aufgabe dampf|protokoll|beide] [--nur id,id] [--kein-denken]
"""

import argparse
import datetime
import json
import os
import re
import sys
import time

from openai import OpenAI

import proben
import prompts_lokal
from vergleich import (BASE_URL, DAMPF_PROMPT, HERE, IDENT, PROTOKOLL_SYSTEM_PROMPT, frage, lms,
                       ram_frei_gb)

WT = prompts_lokal.WOCHENTAGE


def _trifft(gruppen: list[list[str]], low: str) -> list[str]:
    return [g[0] for g in gruppen if not any(w.lower() in low for w in g)]


def pruefe(probe: dict, roh: str, sauber: str) -> dict:
    # 9.12.2026 und 09.12.2026 gelten als gleich
    low = re.sub(r"\b(\d)\.(?=\d{1,2}\.\d{4})", r"0\1.", sauber.lower())
    low = re.sub(r"\b(\d{2})\.(\d)\.(?=\d{4})", r"\1.0\2.", low)
    fehlt = _trifft(probe["muss"], low)
    rep = probe.get("reparatur", [])
    rep_fehlt = _trifft(rep, low)
    return {
        "treffer": f"{len(probe['muss']) - len(fehlt)}/{len(probe['muss'])}",
        "fehlt": fehlt,
        "reparatur": f"{len(rep) - len(rep_fehlt)}/{len(rep)}" if rep else "",
        "reparatur_fehlt": rep_fehlt,
        "verboten": [w for w in probe["darf_nicht"] if w.lower() in low],
        # Formfehler, die erst die Nachbearbeitung beseitigt hat
        "roh_verboten": [w for w in probe["darf_nicht"]
                         if w.lower() in roh.lower() and w.lower() not in low],
    }


def auftraege(variante: str, aufgabe: str, transkripte: dict) -> list[dict]:
    out = []
    if aufgabe in ("dampf", "beide"):
        for p in proben.DAMPF_PROBEN:
            t = transkripte[f"dampf/{p['id']}"]["text"]
            if variante == "standard":
                out.append(dict(probe=p, gruppe="dampf", system=DAMPF_PROMPT, user=t, temp=0.4))
            else:
                out.append(dict(probe=p, gruppe="dampf", system=prompts_lokal.DAMPF_SYSTEM,
                                user=prompts_lokal.dampf_user(t), temp=0.2))
    if aufgabe in ("protokoll", "beide"):
        for p in proben.PROTOKOLL_PROBEN:
            t = transkripte[f"protokoll/{p['id']}"]["text"]
            tag = datetime.date.fromisoformat(p["datum"])
            if variante == "standard":
                user = f"Aufnahmedatum: {WT[tag.weekday()]}, {tag:%d.%m.%Y}\n\n{t}"
                out.append(dict(probe=p, gruppe="protokoll", system=PROTOKOLL_SYSTEM_PROMPT,
                                user=user, temp=0.2))
            else:
                out.append(dict(probe=p, gruppe="protokoll", system=prompts_lokal.PROTOKOLL_SYSTEM,
                                user=prompts_lokal.protokoll_user(t, tag), temp=0.1))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("modell")
    ap.add_argument("--gpu", default="off")
    ap.add_argument("--ctx", default="8192")
    ap.add_argument("--variante", default="beide", choices=["standard", "lokal", "beide"])
    ap.add_argument("--aufgabe", default="beide", choices=["dampf", "protokoll", "beide"])
    ap.add_argument("--nur", default="", help="nur diese Proben-IDs (Komma-getrennt)")
    ap.add_argument("--kein-denken", action="store_true")
    ap.add_argument("--marke", default="", help="Zusatz für den Dateinamen (z. B. v2)")
    args = ap.parse_args()

    with open(os.path.join(HERE, "transkripte.json"), encoding="utf-8") as f:
        transkripte = json.load(f)

    lms("unload", "--all")
    time.sleep(2)
    ram_vor = ram_frei_gb()
    res = lms("load", args.modell, "--gpu", args.gpu, "-c", args.ctx, "--identifier", IDENT, "-y")
    if res.returncode != 0:
        print("LADEN FEHLGESCHLAGEN:\n", res.stdout[-1500:], res.stderr[-1500:])
        sys.exit(1)
    ram = round(ram_vor - ram_frei_gb(), 1)

    client = OpenAI(base_url=BASE_URL, api_key="lm-studio", timeout=1800)
    extra = {"reasoning_effort": "none"} if args.kein_denken else {}
    frage(client, "Antworte kurz.", "Sag Hallo.", 0.0, extra)

    nur = {x for x in args.nur.split(",") if x}
    varianten = ["standard", "lokal"] if args.variante == "beide" else [args.variante]
    os.makedirs(os.path.join(HERE, "ergebnisse", "runde2"), exist_ok=True)
    for variante in varianten:
        laeufe = []
        for a in auftraege(variante, args.aufgabe, transkripte):
            p = a["probe"]
            if nur and p["id"] not in nur:
                continue
            r = frage(client, a["system"], a["user"], a["temp"], extra)
            r["roh"] = r.pop("text")
            r["text"] = prompts_lokal.saeubern(r["roh"]) if variante == "lokal" else r["roh"]
            r.update(gruppe=a["gruppe"], id=p["id"], pruefung=pruefe(p, r["roh"], r["text"]))
            laeufe.append(r)
            pr = r["pruefung"]
            print(f"{variante:8} {a['gruppe']:9} {p['id']:9} {r['sek_gesamt']:6.1f} s  "
                  f"erstes Zeichen {r['sek_bis_erstes_zeichen']:5.1f} s  {r['tokens_ein']} ein  "
                  f"Prüfwörter {pr['treffer']}  fehlt {pr['fehlt']}  verboten {pr['verboten']}",
                  flush=True)
        name = args.modell.replace("/", "_") + f"__gpu-{args.gpu}__{variante}"
        name += "__ohne-denken" if args.kein_denken else "__mit-denken"
        if args.marke:
            name += f"__{args.marke}"
        with open(os.path.join(HERE, "ergebnisse", "runde2", name + ".json"), "w",
                  encoding="utf-8") as f:
            json.dump({"modell": args.modell, "gpu": args.gpu, "variante": variante,
                       "kein_denken": args.kein_denken,
                       "marke": args.marke, "ram_belegt_gb": ram, "laeufe": laeufe},
                      f, ensure_ascii=False, indent=2)

    lms("unload", "--all")


if __name__ == "__main__":
    main()
