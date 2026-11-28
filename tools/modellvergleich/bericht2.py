# Copyright (c) 2026 Thorben Meier. MIT License.
"""Fasst die Läufe der Runde 2 zusammen → ergebnisse/Bericht-Runde2.md.

Die Prüfwörter werden beim Berichten neu ausgewertet, damit alle Läufe nach
denselben Regeln beurteilt werden.
"""

import glob
import json
import os

import proben
from runde2 import pruefe

HERE = os.path.dirname(os.path.abspath(__file__))
ERG = os.path.join(HERE, "ergebnisse")
PROBEN = {("dampf", p["id"]): p for p in proben.DAMPF_PROBEN}
PROBEN.update({("protokoll", p["id"]): p for p in proben.PROTOKOLL_PROBEN})
SPALTEN = list(PROBEN)

laeufe = []
for pfad in sorted(glob.glob(os.path.join(ERG, "runde2", "*.json"))):
    with open(pfad, encoding="utf-8") as f:
        e = json.load(f)
    for r in e["laeufe"]:
        r["pruefung"] = pruefe(PROBEN[(r["gruppe"], r["id"])], r["roh"], r["text"])
    laeufe.append(e)


def titel(e: dict) -> str:
    geraet = "Prozessor" if e["gpu"] == "off" else "Grafikkarte"
    prompt = "App-Prompt" if e["variante"] == "standard" else f"lokaler Prompt {e.get('marke') or 'v1'}"
    denken = "" if e.get("kein_denken", False) else " · mit Denkmodus"
    return f"{e['modell']} · {geraet} · {prompt}{denken}"


kopf = " | ".join(f"{g} {i}" for g, i in SPALTEN)
z = ["# Modellvergleich lokale KI – Runde 2", "",
     "Eingabe: von der Windows-Sprachausgabe vorgelesene Proben, transkribiert mit Whisper "
     "small (wie in der App). „App-Prompt“ = heutiger Prompt, „lokaler Prompt“ = "
     "prompts_lokal.py (v1 mit Kalender, v2 mit vorab ausgerechneten Daten im Transkript).", "",
     "## Prüfwörter (gefunden / erwartet)", "",
     f"| Lauf | {kopf} |", "|---|" + "---|" * len(SPALTEN)]
for e in laeufe:
    by = {(r["gruppe"], r["id"]): r for r in e["laeufe"]}
    zellen = []
    for s in SPALTEN:
        if s not in by:
            zellen.append("–")
            continue
        p = by[s]["pruefung"]
        zellen.append(p["treffer"] + (" ⚠" if p["verboten"] else ""))
    z.append(f"| {titel(e)} | " + " | ".join(zellen) + " |")

z += ["", "## Zeiten in Sekunden", "", f"| Lauf | {kopf} |", "|---|" + "---|" * len(SPALTEN)]
for e in laeufe:
    by = {(r["gruppe"], r["id"]): r for r in e["laeufe"]}
    z.append(f"| {titel(e)} | "
             + " | ".join(str(by[s]["sek_gesamt"]) if s in by else "–" for s in SPALTEN) + " |")

z += ["", "## Ausgaben im Wortlaut", ""]
for e in laeufe:
    z += [f"### {titel(e)}", ""]
    for r in e["laeufe"]:
        p = r["pruefung"]
        kopfzeile = (f"**{r['gruppe']} / {r['id']}** — {r['sek_gesamt']} s, "
                     f"{r['tokens_ein']} Tokens ein, {r['tokens_aus']} aus, Prüfwörter {p['treffer']}")
        for name, key in (("fehlt", "fehlt"), ("unerwünscht", "verboten"),
                          ("Hörfehler nicht repariert", "reparatur_fehlt"),
                          ("erst durch Nachbearbeitung beseitigt", "roh_verboten")):
            if p[key]:
                kopfzeile += f"; {name}: {', '.join(repr(x) for x in p[key])}"
        z += [kopfzeile, "", "```text", r["text"], "```", ""]

with open(os.path.join(ERG, "Bericht-Runde2.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(z))
print(f"{len(laeufe)} Läufe → {os.path.join(ERG, 'Bericht-Runde2.md')}")
