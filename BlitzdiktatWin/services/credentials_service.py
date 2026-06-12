# Copyright (c) 2026 Thorben Meier. MIT License.
import keyring

_SERVICE = "BlitzdiktatWin"
_OPENAI_KEY = "openai_api_key"


def save_api_key(api_key: str) -> None:
    keyring.set_password(_SERVICE, _OPENAI_KEY, api_key)


def load_api_key() -> str | None:
    return keyring.get_password(_SERVICE, _OPENAI_KEY)


def delete_api_key() -> None:
    try:
        keyring.delete_password(_SERVICE, _OPENAI_KEY)
    except Exception:
        pass


def is_configured() -> bool:
    key = load_api_key()
    return bool(key and key.strip())


def masked_display(key: str) -> str:
    if not key:
        return ""
    if len(key) > 8:
        return key[:4] + " ••••••••"
    return "••••••••"
