# Copyright (c) 2026 Thorben Meier. MIT License.
"""Erzeugt realistische Transkripte für Runde 2.

Jede Probe aus proben.py wird von der Windows-Sprachausgabe (Hedda, de-DE)
vorgelesen und danach mit dem Whisper-Modell der App transkribiert – über
dieselbe Funktion, die auch Blitzdiktat benutzt. Ergebnis: transkripte.json.

Aufruf:  python sprechen.py [whisper-modell]     (Standard: small)
"""

import json
import os
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "BlitzdiktatWin"))

from services.local_transcription_service import transcribe_local  # noqa: E402

import proben  # noqa: E402

PS = r"""
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.SelectVoice('Microsoft Hedda Desktop')
$f = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(16000, 'Sixteen', 'Mono')
$s.SetOutputToWaveFile($args[1], $f)
$s.Speak([IO.File]::ReadAllText($args[0], [Text.Encoding]::UTF8))
$s.Dispose()
"""


def vorlesen(text: str, wav: str) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        txt = os.path.join(tmp, "t.txt")
        ps1 = os.path.join(tmp, "s.ps1")
        with open(txt, "w", encoding="utf-8") as f:
            f.write(text)
        with open(ps1, "w", encoding="utf-8-sig") as f:
            f.write(PS)
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps1, txt, wav],
            check=True, timeout=600,
        )


def main() -> None:
    modell = sys.argv[1] if len(sys.argv) > 1 else "small"
    audio = os.path.join(HERE, "ergebnisse", "audio")
    os.makedirs(audio, exist_ok=True)
    ziel = os.path.join(HERE, "transkripte.json")
    out: dict[str, dict] = {}
    if os.path.exists(ziel):  # vorhandene Transkripte behalten, nur neue Proben ergänzen
        with open(ziel, encoding="utf-8") as f:
            out = json.load(f)
    for gruppe, liste in (("dampf", proben.DAMPF_PROBEN), ("protokoll", proben.PROTOKOLL_PROBEN)):
        for p in liste:
            key = f"{gruppe}/{p['id']}"
            if key in out:
                continue
            wav = os.path.join(audio, f"{gruppe}_{p['id']}.wav")
            if not os.path.exists(wav):
                vorlesen(p["gesprochen"], wav)
            t0 = time.perf_counter()
            text = transcribe_local(wav, modell, "de", None)
            out[key] = {"whisper": modell, "sek": round(time.perf_counter() - t0, 1), "text": text}
            print(f"{key}: {out[key]['sek']} s\n{text}\n", flush=True)
    with open(ziel, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
