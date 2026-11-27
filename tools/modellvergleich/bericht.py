# Copyright (c) 2026 Thorben Meier. MIT License.
"""Fasst alle Läufe unter ergebnisse/ zu einem Markdown-Bericht zusammen.

Aufruf:  python bericht.py   → schreibt ergebnisse/Bericht.md
"""

import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ERG = os.path.join(HERE, "ergebnisse")

laeufe = []
for pfad in sorted(glob.glob(os.path.join(ERG, "*.json"))):
    with open(pfad, encoding="utf-8") as f:
        laeufe.append(json.load(f))


def titel(e: dict) -> str:
    geraet = "Prozessor" if e["gpu"] == "off" else f"Grafikkarte ({e['gpu']})"
    return f"{e['modell']} · {geraet}"


z = ["# Modellvergleich lokale KI", "",
     "Echte Blitzdiktat-Prompts, deutsche Beispiel-Diktate, gemessen über LM Studio.", "",
     "## Zeiten in Sekunden (gesamt je Aufgabe)", ""]
ids = [("verbessern", "Blitzdiktat+"), ("dampf", "$%&!"), ("emoji", ":)"),
       ("protokoll", "Protokoll"), ("vokabular", "Vokabular")]
z.append("| Modell | Laden | RAM | " + " | ".join(n for _, n in ids) + " | Tokens/s |")
z.append("|---|---|---|" + "---|" * (len(ids) + 1))
for e in laeufe:
    by = {r["id"]: r for r in e["laeufe"]}
    tps = [r["tokens_pro_sek"] for r in e["laeufe"] if r.get("tokens_pro_sek")]
    z.append(
        f"| {titel(e)} | {e['lade_sek']} | {e['ram_belegt_gb']} GB | "
        + " | ".join(str(by[i]["sek_gesamt"]) if i in by else "–" for i, _ in ids)
        + f" | {round(sum(tps) / len(tps), 1) if tps else '–'} |"
    )

z += ["", "## Prüfwörter (gefunden / erwartet)", "",
      "| Modell | " + " | ".join(n for _, n in ids) + " |",
      "|---|" + "---|" * len(ids)]
for e in laeufe:
    by = {r["id"]: r for r in e["laeufe"]}
    zellen = []
    for i, _ in ids:
        if i not in by:
            zellen.append("–")
            continue
        p = by[i]["pruefung"]
        zelle = p["treffer"]
        if p["verboten"]:
            zelle += " ⚠ " + ", ".join(p["verboten"])
        if p.get("json_ok") is False:
            zelle += " ⚠ kein JSON"
        zellen.append(zelle)
    z.append(f"| {titel(e)} | " + " | ".join(zellen) + " |")

z += ["", "## Ausgaben im Wortlaut", ""]
for e in laeufe:
    z += [f"### {titel(e)}", ""]
    for r in e["laeufe"]:
        p = r["pruefung"]
        z += [f"**{r['name']}** — {r['sek_gesamt']} s, erstes Zeichen nach "
              f"{r['sek_bis_erstes_zeichen']} s, {r['tokens_aus']} Tokens"
              + (f", fehlt: {', '.join(p['fehlt'])}" if p["fehlt"] else ""),
              "", "```text", r["text"], "```", ""]

with open(os.path.join(ERG, "Bericht.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(z))
print(f"{len(laeufe)} Läufe → {os.path.join(ERG, 'Bericht.md')}")
