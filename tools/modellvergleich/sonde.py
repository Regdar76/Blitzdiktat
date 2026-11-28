# Copyright (c) 2026 Thorben Meier. MIT License.
"""Kurzsonde: zeigt live, ob ein geladenes Modell denkt und wie schnell es schreibt.

Aufruf:  python sonde.py [max_tokens] [reasoning_effort]
Erwartet ein mit `lms load ... --identifier bench` geladenes Modell.
"""

import sys
import time

from openai import OpenAI

max_tokens = int(sys.argv[1]) if len(sys.argv) > 1 else 120
effort = sys.argv[2] if len(sys.argv) > 2 else ""

client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio", timeout=600)
t0 = time.perf_counter()
n_denk = n_text = 0
t_text = None
text = []
stream = client.chat.completions.create(
    model="bench",
    messages=[
        {"role": "system", "content": "Korrigiere Rechtschreibung und Grammatik. Gib NUR den Text zurück."},
        {"role": "user", "content": "moin zusammen das sommerfest findet am zwölften juni ab sechzehn uhr statt"},
    ],
    temperature=0.3, max_tokens=max_tokens, stream=True,
    stream_options={"include_usage": True},
    extra_body={"reasoning_effort": effort} if effort else None,
)
usage = None
for chunk in stream:
    if chunk.usage:
        usage = chunk.usage
    if not chunk.choices:
        continue
    d = chunk.choices[0].delta
    r = getattr(d, "reasoning_content", None) or (d.model_extra or {}).get("reasoning")
    if r:
        n_denk += 1
    if d.content:
        if t_text is None:
            t_text = time.perf_counter() - t0
        n_text += 1
        text.append(d.content)
dt = time.perf_counter() - t0
print(f"gesamt {dt:.1f} s | Denk-Stücke {n_denk} | Text-Stücke {n_text} | erstes Textzeichen nach {t_text}")
print("usage:", usage)
print("TEXT:", "".join(text)[:400])
