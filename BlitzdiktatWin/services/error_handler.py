# Copyright (c) 2026 Thorben Meier. MIT License.
"""
Übersetzt OpenAI-SDK-Exceptions in kurze, deutsche Fehlermeldungen.
"""

try:
    from openai import AuthenticationError, APIConnectionError, RateLimitError, APIStatusError
    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False


def _is_quota_exceeded(exc) -> bool:
    """Prüft ob es sich um Kontingent-Erschöpfung handelt (≠ echtes RPM-Limit)."""
    # 1) Strukturierter Body (neuere SDK-Versionen)
    try:
        body = getattr(exc, "body", None) or {}
        if isinstance(body, dict):
            error_obj = body.get("error", {})
            if isinstance(error_obj, dict):
                code = (error_obj.get("code") or error_obj.get("type") or "").lower()
                if "quota" in code or "insufficient" in code:
                    return True
    except Exception:
        pass
    # 2) Freitext in exc.message oder str(exc)
    haystack = ((getattr(exc, "message", "") or "") + " " + str(exc)).lower()
    return any(kw in haystack for kw in (
        "exceeded your current quota",
        "insufficient_quota",
        "you exceeded",
        "billing",
    ))


def friendly_message(exc: Exception) -> str:
    if not _OPENAI_AVAILABLE:
        return str(exc).split("\n")[0][:120]

    if isinstance(exc, AuthenticationError):
        return "API Key ungültig. Bitte in den Einstellungen einen gültigen Key eintragen."

    if isinstance(exc, APIConnectionError):
        return "Keine Verbindung zu OpenAI. Bitte Internetverbindung prüfen."

    if isinstance(exc, RateLimitError):
        if _is_quota_exceeded(exc):
            return (
                "OpenAI-Kontingent erschöpft — kein Guthaben oder Plan abgelaufen. "
                "Bitte auf platform.openai.com/account/billing prüfen."
            )
        # Echtes Anfrage-Limit (RPM/TPM) — kurz warten reicht
        return "OpenAI Anfrage-Limit erreicht. Bitte 1–2 Minuten warten und nochmal versuchen."

    if isinstance(exc, APIStatusError):
        detail = (getattr(exc, "message", "") or "").strip()
        return f"OpenAI-Fehler {exc.status_code}: {detail[:100]}" if detail else f"OpenAI-Fehler {exc.status_code}"

    msg = str(exc).split("\n")[0].strip()
    return msg[:120] if msg else "Unbekannter Fehler"
