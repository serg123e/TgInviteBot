"""Tests for Config (pydantic-settings)."""

import os
from unittest.mock import patch

from bot.config import Config


def test_defaults():
    with patch.dict(os.environ, {}, clear=True):
        cfg = Config()
    assert cfg.lang == "en"
    assert cfg.bot_token == ""
    assert cfg.admin_chat_id == 0
    assert cfg.default_timeout_minutes == 15
    assert cfg.default_ai_validation is True
    assert cfg.default_ban_on_remove is False


def test_env_override():
    env = {
        "BOT_LANG": "en",
        "BOT_TOKEN": "tok123",
        "ADMIN_CHAT_ID": "42",
        "DEFAULT_TIMEOUT_MINUTES": "60",
        "DEFAULT_AI_VALIDATION": "false",
    }
    with patch.dict(os.environ, env, clear=True):
        cfg = Config()
    assert cfg.lang == "en"
    assert cfg.bot_token == "tok123"
    assert cfg.admin_chat_id == 42
    assert cfg.default_timeout_minutes == 60
    assert cfg.default_ai_validation is False


def test_bool_truthy_values():
    for val in ("true", "True", "1", "yes", "YES"):
        with patch.dict(os.environ, {"DEFAULT_BAN_ON_REMOVE": val}, clear=True):
            cfg = Config()
        assert cfg.default_ban_on_remove is True, f"Expected True for {val!r}"


def test_bool_falsy_values():
    for val in ("false", "0", "no"):
        with patch.dict(os.environ, {"DEFAULT_AI_VALIDATION": val}, clear=True):
            cfg = Config()
        assert cfg.default_ai_validation is False, f"Expected False for {val!r}"
