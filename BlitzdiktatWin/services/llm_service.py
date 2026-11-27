# Copyright (c) 2026 Thorben Meier. MIT License.
import asyncio
import datetime
import json as _json
from typing import TYPE_CHECKING

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
    AuthenticationError,
    BadRequestError,
    OpenAI,
)

from . import credentials_service, local_server, output_cleanup, prompts
from .credentials_service import load_api_key
from .date_annotator import annotate_dates

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


# ── KI-Anbieter ─────────────────────────────────────────────────────────────
# "openai": OpenAI mit API Key (Standard).
# "custom": eigener, OpenAI-kompatibler Server – z. B. LM Studio auf demselben
#           Rechner. Dort läuft ein Modell für alle Aufgaben; ein API Key ist
#           optional.
PROVIDER_OPENAI = "openai"
PROVIDER_CUSTOM = "custom"
DEFAULT_CUSTOM_BASE_URL = "http://localhost:1234/v1"

# Lokale Modelle auf dem Prozessor brauchen für ein langes Protokoll Minuten.
_CUSTOM_TIMEOUT = 600.0

_provider = PROVIDER_OPENAI
_custom_base_url = DEFAULT_CUSTOM_BASE_URL
_custom_model = ""
_custom_disable_thinking = True


def configure_provider(
    provider: str = PROVIDER_OPENAI,
    base_url: str = "",
    model: str = "",
    disable_thinking: bool = True,
) -> None:
    """Legt fest, wer die Textverarbeitung übernimmt."""
    global _provider, _custom_base_url, _custom_model, _custom_disable_thinking
    _provider = PROVIDER_CUSTOM if provider == PROVIDER_CUSTOM else PROVIDER_OPENAI
    _custom_base_url = normalize_base_url(base_url) or DEFAULT_CUSTOM_BASE_URL
    _custom_model = (model or "").strip()
    _custom_disable_thinking = bool(disable_thinking)


def normalize_base_url(url: str) -> str:
    """'localhost:1234' → 'http://localhost:1234/v1' (Schema und /v1 ergänzen)."""
    url = (url or "").strip().rstrip("/")
    if not url:
        return ""
    if "://" not in url:
        url = "http://" + url
    scheme, rest = url.split("://", 1)
    if "/" not in rest:
        url = f"{scheme}://{rest}/v1"
    return url


def is_custom() -> bool:
    return _provider == PROVIDER_CUSTOM


def config_problem() -> str | None:
    """Kurze Meldung, falls die Textverarbeitung nicht eingerichtet ist – sonst None."""
    if is_custom():
        if not _custom_model:
            return "Eigener KI-Server: kein Modell gewählt — Einstellungen öffnen"
        return None
    key = load_api_key()
    if not (key and key.strip()):
        return "API Key fehlt — Einstellungen öffnen"
    return None


def is_available() -> bool:
    return config_problem() is None


def list_models(base_url: str, api_key: str = "", timeout: float = 5.0) -> list[str]:
    """Fragt einen OpenAI-kompatiblen Server nach seinen Modellen (Verbindungstest)."""
    client = OpenAI(
        base_url=normalize_base_url(base_url) or DEFAULT_CUSTOM_BASE_URL,
        api_key=(api_key or "").strip() or "nicht-noetig",
        timeout=timeout,
        max_retries=0,
    )
    names = sorted(m.id for m in client.models.list().data)
    # Einbettungs-Modelle können keinen Text schreiben.
    return [n for n in names if "embed" not in n.lower()]


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


async def dampf_ablassen(text: str, system_prompt: str = "") -> str:
    """system_prompt: eigener Prompt des Nutzers; leer = eingebauter Prompt."""
    if system_prompt:
        result = await _complete(text, system_prompt, model=_model_quality, temperature=0.4)
    elif is_custom():
        result = await _complete(
            prompts.dampf_local_user(text), prompts.DAMPF_LOCAL_SYSTEM_PROMPT,
            model=_model_quality, temperature=0.2,
        )
    else:
        result = await _complete(
            text, prompts.DAMPF_SYSTEM_PROMPT, model=_model_quality, temperature=0.4,
        )
    return output_cleanup.strip_wrapping(result)


_WEEKDAYS_DE = [
    "Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag",
]


async def protokoll(text: str, system_prompt: str = "", today: datetime.date | None = None) -> str:
    """system_prompt: eigener Prompt des Nutzers; leer = eingebauter Prompt."""
    today = today or datetime.date.today()
    recording_date = f"{_WEEKDAYS_DE[today.weekday()]}, {today.strftime('%d.%m.%Y')}"
    # Relative Zeitangaben ("nächsten Freitag") rechnet die App vorab aus und
    # schreibt das Datum in Klammern dahinter – Modelle verrechnen sich dabei.
    annotated = annotate_dates(text, today)

    if not system_prompt and is_custom():
        result = await _complete(
            prompts.protokoll_local_user(annotated, recording_date),
            prompts.PROTOKOLL_LOCAL_SYSTEM_PROMPT,
            model=_model_quality, temperature=0.1,
        )
    else:
        hint = f"{prompts.DATE_HINT}\n\n" if annotated != text else ""
        dated = f"Aufnahmedatum: {recording_date}\n\n{hint}{annotated}"
        result = await _complete(
            dated, system_prompt or prompts.PROTOKOLL_SYSTEM_PROMPT,
            model=_model_quality, temperature=0.2,
        )

    result = output_cleanup.clean_protocol(result)
    if is_custom():
        result += f"\n\n---\n\n{prompts.LOCAL_PROTOCOL_NOTE}"
    return result


async def add_emojis(text: str, density: str = "mittel") -> str:
    prompt = _build_emoji_prompt(density)
    return await _complete(text, prompt, model=_model_fast, temperature=0.3)


async def _complete(text: str, system_prompt: str, model: str, temperature: float) -> str:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text},
    ]
    if is_custom():
        content = await _complete_custom(messages, temperature)
    else:
        api_key = load_api_key()
        if not api_key:
            raise LLMError("OpenAI API Key fehlt. Bitte in den Einstellungen hinterlegen.")
        # "async with" schließt die Verbindung, bevor der Aufrufer seine
        # Ereignisschleife beendet – sonst meldet httpx beim Aufräumen
        # "Event loop is closed".
        async with AsyncOpenAI(api_key=api_key, timeout=60.0, max_retries=2) as client:
            response = await client.chat.completions.create(
                model=model, messages=messages, temperature=temperature,
            )
        content = response.choices[0].message.content

    content = output_cleanup.strip_reasoning(content or "")
    if not content:
        raise LLMError("Keine Antwort erhalten. Bitte nochmal versuchen.")
    return content


async def _complete_custom(messages: list[dict], temperature: float) -> str | None:
    """Anfrage an den eigenen Server; Fehler werden in klare Meldungen übersetzt."""
    if not _custom_model:
        raise LLMError("Eigener KI-Server: kein Modell gewählt. Bitte in den Einstellungen wählen.")
    client_args = dict(
        base_url=_custom_base_url,
        api_key=credentials_service.load_custom_api_key() or "nicht-noetig",
        timeout=_CUSTOM_TIMEOUT,
        max_retries=0,
    )
    kwargs: dict = dict(model=_custom_model, messages=messages, temperature=temperature)
    # Viele lokale Modelle (Gemma 4, Qwen 3.5) "denken" von sich aus erst
    # still nach – das kostet auf dem Prozessor 25–40 s je Diktat, ohne dass
    # das Ergebnis besser wird. Deshalb abschalten.
    extra = {"reasoning_effort": "none"} if _custom_disable_thinking else None

    async def request():
        async with AsyncOpenAI(**client_args) as client:
            try:
                return await client.chat.completions.create(**kwargs, extra_body=extra)
            except BadRequestError:
                if not extra:
                    raise
                # Server kennt den Parameter nicht → ohne ihn noch einmal.
                return await client.chat.completions.create(**kwargs)

    try:
        try:
            response = await request()
        except APITimeoutError:
            raise
        except APIConnectionError:
            # Läuft die KI auf diesem Rechner (LM Studio), ist nach einem
            # Neustart nur der Server aus → selbst starten, einmal wiederholen.
            started = await asyncio.to_thread(local_server.ensure_running, _custom_base_url)
            if not started:
                raise
            response = await request()
    except APITimeoutError as e:
        raise LLMError("Eigener KI-Server hat nicht rechtzeitig geantwortet (Zeitlimit 10 Minuten).") from e
    except APIConnectionError as e:
        if local_server.is_local_url(_custom_base_url):
            raise LLMError(
                "Lokale KI nicht erreichbar. LM Studio einmal öffnen, dann erneut versuchen."
            ) from e
        raise LLMError(
            f"Eigener KI-Server nicht erreichbar ({_custom_base_url[:60]}). Läuft er?"
        ) from e
    except AuthenticationError as e:
        raise LLMError("Eigener KI-Server lehnt den API Key ab. Bitte in den Einstellungen prüfen.") from e
    except APIStatusError as e:
        detail = (getattr(e, "message", "") or "").strip().replace("\n", " ")
        raise LLMError(f"Eigener KI-Server meldet Fehler {e.status_code}: {detail[:70]}") from e
    return response.choices[0].message.content


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
        "- Behalte die Anrede bei (du, ihr oder Sie)\n"
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
