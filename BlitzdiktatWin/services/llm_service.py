# Copyright (c) 2026 Thorben Meier. MIT License.
import datetime
import json as _json
from typing import TYPE_CHECKING

from openai import AsyncOpenAI
from .credentials_service import load_api_key

if TYPE_CHECKING:
    from app_state import TextImprovementSettings


class LLMError(Exception):
    pass


# ── Modellauswahl ───────────────────────────────────────────────────────────
# Standardwerte — überschreibbar in settings.json über die Felder
# "openai_model_fast" und "openai_model_quality" (leer = Standard).
DEFAULT_MODEL_FAST = "gpt-4o-mini"      # Textverbesserung, Emojis, Vokabular
DEFAULT_MODEL_QUALITY = "gpt-4o"        # Dampf ablassen, Protokoll

_model_fast = DEFAULT_MODEL_FAST
_model_quality = DEFAULT_MODEL_QUALITY


def set_models(fast: str = "", quality: str = "") -> None:
    """Setzt die verwendeten Chat-Modelle. Leere Strings = Standardmodell."""
    global _model_fast, _model_quality
    _model_fast = (fast or "").strip() or DEFAULT_MODEL_FAST
    _model_quality = (quality or "").strip() or DEFAULT_MODEL_QUALITY


_EXTRACT_TERMS_PROMPT = (
    "Extrahiere alle Eigennamen, Firmennamen, Produktnamen, Ortsnamen und Fachbegriffe "
    "aus dem folgenden Text. Gib NUR eine JSON-Liste von Strings zurück, z. B. "
    '[\"OpenAI\", \"München\", \"Bauprojekt Nord\"]. '
    "Keine Erklärungen. Wenn keine relevanten Begriffe vorhanden sind, gib [] zurück."
)


async def extract_terms(text: str) -> list[str]:
    """Extrahiert Eigennamen und Fachbegriffe aus einem Transkript (im Hintergrund)."""
    try:
        raw = await _complete(text, _EXTRACT_TERMS_PROMPT, model=_model_fast, temperature=0.0)
        terms = _json.loads(raw)
        return [str(t).strip() for t in terms if isinstance(t, str) and t.strip()]
    except Exception:
        return []


async def improve(text: str, settings: "TextImprovementSettings") -> str:
    prompt = _build_improvement_prompt(settings)
    return await _complete(text, prompt, model=_model_fast, temperature=0.3)


async def dampf_ablassen(text: str, system_prompt: str) -> str:
    return await _complete(text, system_prompt, model=_model_quality, temperature=0.4)


_WEEKDAYS_DE = [
    "Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag",
]


async def protokoll(text: str, system_prompt: str) -> str:
    # Aufnahmedatum mitgeben, damit das Modell das Datumsfeld füllen und
    # relative Zeitangaben ("nächsten Freitag") in konkrete Termine umrechnen kann.
    now = datetime.datetime.now()
    dated = (
        f"Aufnahmedatum: {_WEEKDAYS_DE[now.weekday()]}, {now.strftime('%d.%m.%Y')}\n\n{text}"
    )
    return await _complete(dated, system_prompt, model=_model_quality, temperature=0.2)


async def add_emojis(text: str, density: str = "mittel") -> str:
    prompt = _build_emoji_prompt(density)
    return await _complete(text, prompt, model=_model_fast, temperature=0.3)


async def _complete(text: str, system_prompt: str, model: str, temperature: float) -> str:
    api_key = load_api_key()
    if not api_key:
        raise LLMError("OpenAI API Key fehlt. Bitte in den Einstellungen hinterlegen.")

    client = AsyncOpenAI(api_key=api_key, timeout=60.0, max_retries=2)
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        temperature=temperature,
    )

    content = response.choices[0].message.content
    if not content or not content.strip():
        raise LLMError("Keine Antwort erhalten. Bitte nochmal versuchen.")
    return content.strip()


def _build_improvement_prompt(settings) -> str:
    if settings.system_prompt:
        prompt = settings.system_prompt
        if settings.custom_terms:
            terms = ", ".join(settings.custom_terms)
            prompt += f"\n\nWichtig: Diese Eigennamen und Fachbegriffe müssen exakt so geschrieben werden: {terms}"
        return prompt

    tone_map = {
        "formal": "Verwende einen formellen, professionellen Ton",
        "neutral": "Verwende einen neutralen, klaren Ton",
        "casual": "Verwende einen lockeren, natürlichen Ton",
    }
    tone = tone_map.get(settings.tone, tone_map["neutral"])

    prompt = (
        "Du bist ein Lektor und Schreibassistent. Verbessere den folgenden Text:\n"
        "- Korrigiere Rechtschreibung und Grammatik\n"
        "- Verbessere die Formulierung und den Lesefluss\n"
        "- Behalte die ursprüngliche Bedeutung bei\n"
        f"- {tone}\n"
        "- Gib NUR den verbesserten Text zurück, keine Erklärungen"
    )

    if settings.custom_terms:
        terms = ", ".join(settings.custom_terms)
        prompt += f"\n\nWichtig: Diese Eigennamen und Fachbegriffe müssen exakt so geschrieben werden: {terms}"

    if settings.context:
        prompt += f"\n\nKontext: {settings.context}"

    return prompt


def _build_emoji_prompt(density: str) -> str:
    density_map = {
        "wenig": "Setze nur vereinzelt Emojis ein, maximal 1-2 pro Absatz.",
        "mittel": "Setze regelmäßig passende Emojis ein, etwa alle 1-2 Sätze.",
        "viel": "Setze großzügig Emojis ein, gerne mehrere pro Satz.",
    }
    instruction = density_map.get(density, density_map["mittel"])
    return (
        "Du erhältst ein gesprochenes Transkript. Gib den Text möglichst originalgetreu zurück, "
        f"aber füge passende Emojis ein. {instruction} "
        "Korrigiere offensichtliche Sprach- und Grammatikfehler. Behalte den Stil und die Bedeutung bei. "
        "Gib NUR den Text mit Emojis zurück, keine Erklärungen."
    )
