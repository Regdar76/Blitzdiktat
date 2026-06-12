# Copyright (c) 2026 Thorben Meier. MIT License.
import asyncio
import re
from openai import AsyncOpenAI, APIConnectionError, APITimeoutError, APIStatusError
from .credentials_service import load_api_key

# Standardmodell für Online-Transkription — überschreibbar in settings.json
# über das Feld "openai_transcription_model" (leer = Standard).
DEFAULT_TRANSCRIPTION_MODEL = "whisper-1"

_transcription_model = DEFAULT_TRANSCRIPTION_MODEL


def set_transcription_model(name: str = "") -> None:
    """Setzt das Online-Transkriptionsmodell. Leerer String = Standard."""
    global _transcription_model
    _transcription_model = (name or "").strip() or DEFAULT_TRANSCRIPTION_MODEL


def _build_numbered_list(match: re.Match) -> str:
    """Wandelt den Inhalt zwischen 'Aufzählung' und 'Aufzählung Ende' in eine nummerierte Liste um."""
    content = match.group(1).strip()
    # Führende/abschließende Satzzeichen entfernen
    content = re.sub(r'^[,;.\s]+|[,;.\s]+$', '', content)
    # Trennzeichen: Komma, Semikolon, Punkt + optional Leerzeichen, " und "
    items = re.split(r'[,;]|(?<!\d)\.(?!\d)|\s+und\s+', content, flags=re.IGNORECASE)
    items = [item.strip().strip('.,;') for item in items if item.strip().strip('.,;')]
    if not items:
        return ""
    return "\n" + "\n".join(f"{i + 1}. {item}" for i, item in enumerate(items)) + "\n"


# Alle Schreibweisen, die Whisper für "Aufzählung" produzieren kann
_AUFZAEHLUNG = r'[Aa]uf(?:z[äa]hlung|zählung|zaehlung)'
_AUFZAEHLUNG_ENDE = _AUFZAEHLUNG + r'[\s,]*[Ee]nde'


def apply_voice_commands(text: str) -> str:
    """Ersetzt gesprochene Steuerkommandos durch Formatierungen (Groß-/Kleinschreibung egal)."""
    # "Aufzählung … Aufzählung Ende" → nummerierte Liste
    # Erlaubt optionale Satzzeichen/Leerzeichen zwischen dem Trigger-Wort und dem Inhalt
    pattern = _AUFZAEHLUNG + r'[,:.!\s]+(.*?)[,:.!\s]*' + _AUFZAEHLUNG_ENDE
    text = re.sub(pattern, _build_numbered_list, text, flags=re.IGNORECASE | re.DOTALL)
    # "Absatz" → Zeilenumbruch (umgebende Satzzeichen/Leerzeichen mitentfernen)
    text = re.sub(r'[,;.!\s]*(?<!\w)[Aa]bsatz(?!\w)[,;.!\s]*', '\n', text)
    return text


def _is_network_error(exc: BaseException) -> bool:
    """Gibt True zurück wenn der Fehler auf eine fehlende Netzwerkverbindung hindeutet."""
    if isinstance(exc, (APIConnectionError, APITimeoutError)):
        return True
    if isinstance(exc, APIStatusError) and exc.status_code in (502, 503, 504):
        return True
    # Fallback: grobe String-Prüfung für nicht-openai-wrapped Netzwerkfehler
    msg = str(exc).lower()
    return any(k in msg for k in ("connection", "timeout", "network", "unreachable", "name or service"))


async def _transcribe_online(
    audio_path: str,
    language: str = "de",
    custom_terms: list[str] | None = None,
) -> str:
    api_key = load_api_key()
    if not api_key:
        raise RuntimeError("OpenAI API Key fehlt. Bitte in den Einstellungen hinterlegen.")

    client = AsyncOpenAI(api_key=api_key, timeout=120.0, max_retries=1)
    prompt = ", ".join(custom_terms) if custom_terms else None

    with open(audio_path, "rb") as f:
        kwargs: dict = dict(model=_transcription_model, file=f, language=language)
        if prompt:
            kwargs["prompt"] = prompt
        response = await client.audio.transcriptions.create(**kwargs)

    return response.text.strip()


def transcribe_sync(
    audio_path: str,
    language: str = "de",
    custom_terms: list[str] | None = None,
    backend: str = "online",
    local_model: str = "small",
) -> tuple[str, str]:
    """Synchroner Einstiegspunkt für Workflow-Threads.

    Gibt (text, hinweis) zurück. hinweis ist ein leerer String wenn alles normal lief,
    oder eine Info-Meldung wenn automatisch auf lokale Transkription umgeschaltet wurde.
    """
    if backend == "local":
        from .local_transcription_service import transcribe_local
        return transcribe_local(audio_path, local_model, language, custom_terms), ""

    loop = asyncio.new_event_loop()
    try:
        text = loop.run_until_complete(
            _transcribe_online(audio_path, language, custom_terms)
        )
        return text, ""
    except Exception as exc:
        if not _is_network_error(exc):
            raise
        # OpenAI nicht erreichbar → lokal versuchen
        try:
            from .local_transcription_service import transcribe_local, AVAILABLE
            if not AVAILABLE:
                raise exc  # lokal auch nicht verfügbar → Original-Fehler weitergeben
            text = transcribe_local(audio_path, local_model, language, custom_terms)
            return text, "OpenAI offline — lokale Transkription verwendet"
        except ImportError:
            raise exc
    finally:
        loop.close()
