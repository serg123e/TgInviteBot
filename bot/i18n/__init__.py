"""Lightweight i18n: English keys as defaults, translations loaded by LANG env var."""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)

_translations: dict[str, str] = {}


def load(lang: str) -> None:
    """Load translation dict for the given language code."""
    global _translations
    if lang == "ru":
        from bot.i18n import ru
        _translations = ru.MESSAGES
        log.info("Loaded translations for lang=%s (%d keys)", lang, len(_translations))
    else:
        _translations = {}
        log.info("Using default language (en)")


def has(key: str) -> bool:
    """Check if a translation exists for the given key."""
    return key in _translations


def t(key: str, **kwargs: object) -> str:
    """Translate a key, falling back to the key itself (English)."""
    text = _translations.get(key, key)
    return text.format(**kwargs) if kwargs else text
