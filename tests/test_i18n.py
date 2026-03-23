"""Verify that every t() key used in the codebase has translations in all languages."""

import ast
import importlib
import os
import re

import pytest

from bot.i18n import SUPPORTED_LANGS, ru


def _extract_t_keys(directory: str) -> set[str]:
    """Extract all string literal first arguments of t() calls from .py files."""
    keys: set[str] = set()
    # Match t("..." including multiline: t(\n  "..."
    pattern = re.compile(r'\bt\(\s*\n?\s*"((?:[^"\\]|\\.)*)"', re.DOTALL)

    for root, _dirs, files in os.walk(directory):
        for fname in files:
            if not fname.endswith(".py"):
                continue
            filepath = os.path.join(root, fname)
            with open(filepath) as f:
                content = f.read()
            for match in pattern.finditer(content):
                # Unescape the string literal
                raw = match.group(1)
                try:
                    key = ast.literal_eval(f'"{raw}"')
                except Exception:
                    key = raw
                keys.add(key)

    return keys


def _get_messages(lang: str) -> dict[str, str]:
    """Import and return MESSAGES dict for a language."""
    module = importlib.import_module(f"bot.i18n.{lang}")
    return module.MESSAGES


def _bot_dir() -> str:
    return os.path.join(os.path.dirname(__file__), "..", "bot")


# --- Per-language coverage ---


@pytest.mark.parametrize("lang", sorted(SUPPORTED_LANGS))
def test_all_t_keys_have_translation(lang):
    """Every t() key used in bot/ must exist in the language's MESSAGES."""
    keys = _extract_t_keys(_bot_dir())
    messages = _get_messages(lang)

    assert len(keys) > 0, "No t() keys found — regex may be broken"

    missing = keys - set(messages.keys())
    assert not missing, (
        f"Missing {lang} translations for {len(missing)} key(s):\n"
        + "\n".join(f"  - {k!r}" for k in sorted(missing))
    )


@pytest.mark.parametrize("lang", sorted(SUPPORTED_LANGS))
def test_no_orphan_translations(lang):
    """Every key in MESSAGES should be used by at least one t() call."""
    keys = _extract_t_keys(_bot_dir())
    messages = _get_messages(lang)

    orphans = set(messages.keys()) - keys
    assert not orphans, (
        f"Orphan {lang} translations (not used in code):\n"
        + "\n".join(f"  - {k!r}" for k in sorted(orphans))
    )


@pytest.mark.parametrize("lang", sorted(SUPPORTED_LANGS))
def test_all_languages_have_same_keys(lang):
    """All languages must have exactly the same set of keys as Russian (reference)."""
    ref_keys = set(ru.MESSAGES.keys())
    messages = _get_messages(lang)
    lang_keys = set(messages.keys())

    missing = ref_keys - lang_keys
    extra = lang_keys - ref_keys

    errors = []
    if missing:
        errors.append(
            f"Keys in ru but missing in {lang}:\n"
            + "\n".join(f"  - {k!r}" for k in sorted(missing))
        )
    if extra:
        errors.append(
            f"Keys in {lang} but missing in ru:\n"
            + "\n".join(f"  - {k!r}" for k in sorted(extra))
        )
    assert not errors, "\n".join(errors)


@pytest.mark.parametrize("lang", sorted(SUPPORTED_LANGS))
def test_placeholders_match(lang):
    """Translated strings must contain the same {placeholders} as the English keys."""
    messages = _get_messages(lang)
    placeholder_re = re.compile(r"\{(\w+)\}")

    mismatches = []
    for key, translation in messages.items():
        key_ph = set(placeholder_re.findall(key))
        trans_ph = set(placeholder_re.findall(translation))
        if key_ph != trans_ph:
            mismatches.append(
                f"  {lang}[{key!r}]: key has {key_ph}, translation has {trans_ph}"
            )

    assert not mismatches, (
        f"Placeholder mismatches in {lang}:\n" + "\n".join(mismatches)
    )


# --- Basic functionality ---


def test_t_fallback_to_english():
    """When no translations are loaded, t() returns the key itself."""
    from bot.i18n import load, t
    load("en")
    assert t("Approve") == "Approve"
    assert t("Hello {name}", name="World") == "Hello World"


def test_t_returns_russian():
    """When Russian is loaded, t() returns the translation."""
    from bot.i18n import load, t
    load("ru")
    assert t("Approve") == "Одобрить"
    assert t("Remove") == "Удалить"
    # Restore
    load("en")


@pytest.mark.parametrize("lang", sorted(SUPPORTED_LANGS))
def test_t_loads_language(lang):
    """Every supported language can be loaded and returns translations."""
    from bot.i18n import load, t
    load(lang)
    messages = _get_messages(lang)
    # Pick first key and verify t() returns the translation
    key = next(iter(messages))
    assert t(key) == messages[key]
    # Restore
    load("en")
