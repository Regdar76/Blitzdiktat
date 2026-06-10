from openai import AsyncOpenAI
from .credentials_service import load_api_key


class LLMError(Exception):
    pass


async def improve(text: str, settings: "TextImprovementSettings") -> str:
    prompt = _build_improvement_prompt(settings)
    return await _complete(text, prompt, model="gpt-4o-mini", temperature=0.3)


async def dampf_ablassen(text: str, system_prompt: str) -> str:
    return await _complete(text, system_prompt, model="gpt-4o", temperature=0.4)


async def protokoll(text: str, system_prompt: str) -> str:
    return await _complete(text, system_prompt, model="gpt-4o", temperature=0.2)


async def add_emojis(text: str, density: str = "mittel") -> str:
    prompt = _build_emoji_prompt(density)
    return await _complete(text, prompt, model="gpt-4o-mini", temperature=0.3)


async def _complete(text: str, system_prompt: str, model: str, temperature: float) -> str:
    api_key = load_api_key()
    if not api_key:
        raise LLMError("OpenAI API Key fehlt. Bitte in den Einstellungen hinterlegen.")

    client = AsyncOpenAI(api_key=api_key)
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
