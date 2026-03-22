"""Verify that every t() key used in the codebase has a Russian translation."""

import ast
import os
import re

from bot.i18n import ru


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


def test_all_t_keys_have_ru_translation():
    """Every t() key used in bot/ must exist in ru.MESSAGES."""
    bot_dir = os.path.join(os.path.dirname(__file__), "..", "bot")
    keys = _extract_t_keys(bot_dir)

    # Remove keys that are not real translation keys (e.g., "ai_system_prompt" check)
    # but keep "ai_system_prompt" since it IS a valid key
    assert len(keys) > 0, "No t() keys found — regex may be broken"

    missing = keys - set(ru.MESSAGES.keys())
    assert not missing, (
        f"Missing Russian translations for {len(missing)} key(s):\n"
        + "\n".join(f"  - {k!r}" for k in sorted(missing))
    )


def test_no_orphan_ru_translations():
    """Every key in ru.MESSAGES should be used by at least one t() call."""
    bot_dir = os.path.join(os.path.dirname(__file__), "..", "bot")
    keys = _extract_t_keys(bot_dir)

    orphans = set(ru.MESSAGES.keys()) - keys
    assert not orphans, (
        "Orphan Russian translations (not used in code):\n"
        + "\n".join(f"  - {k!r}" for k in sorted(orphans))
    )


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
