"""Tests for notifier service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.services.notifier import (
    notify_new_member,
    notify_response,
    notify_timeout,
)
from bot.utils.template import user_display


def _mock_bot(msg_id: int = 42) -> AsyncMock:
    bot = AsyncMock()
    bot.send_message.return_value = MagicMock(message_id=msg_id)
    return bot


class TestUserDisplay:
    def test_with_username(self):
        assert user_display("alice", "Alice", 1) == "@alice"

    def test_with_first_name(self):
        assert user_display(None, "Bob", 2) == "Bob (id: 2)"

    def test_fallback_to_id(self):
        assert user_display(None, None, 3) == "id: 3"


@pytest.mark.asyncio
async def test_notify_new_member():
    bot = _mock_bot(msg_id=99)
    with patch("bot.services.notifier.config", admin_chat_id=-100):
        result = await notify_new_member(bot, 1, "Group", 10, "alice", "Alice")

    assert result == 99
    bot.send_message.assert_called_once()
    text = bot.send_message.call_args[0][1]
    assert "@alice" in text
    assert "Group" in text


@pytest.mark.asyncio
async def test_notify_response_sends_new():
    bot = _mock_bot()
    with patch("bot.services.notifier.config", admin_chat_id=-100):
        await notify_response(
            bot, 1, "Group", 10, "alice", "Alice",
            response_text="I'm Alice, a developer.",
            ai_result={"valid": True, "reason": "Good"},
        )

    bot.send_message.assert_called_once()
    call_kwargs = bot.send_message.call_args
    assert "reply_markup" in call_kwargs.kwargs


@pytest.mark.asyncio
async def test_notify_response_edits_existing():
    bot = _mock_bot()
    with patch("bot.services.notifier.config", admin_chat_id=-100):
        await notify_response(
            bot, 1, "Group", 10, "alice", "Alice",
            response_text="I'm Alice.",
            ai_result={"valid": True, "reason": "OK"},
            admin_message_id=55,
        )

    bot.edit_message_text.assert_called_once()
    bot.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_notify_response_falls_back_on_edit_failure():
    bot = _mock_bot()
    bot.edit_message_text.side_effect = Exception("edit failed")
    with patch("bot.services.notifier.config", admin_chat_id=-100):
        await notify_response(
            bot, 1, "Group", 10, "alice", "Alice",
            response_text="I'm Alice.",
            ai_result=None,
            admin_message_id=55,
        )

    bot.edit_message_text.assert_called_once()
    bot.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_notify_response_ai_rejected():
    bot = _mock_bot()
    with patch("bot.services.notifier.config", admin_chat_id=-100):
        await notify_response(
            bot, 1, "Group", 10, "bob", "Bob",
            response_text="hi",
            ai_result={"valid": False, "reason": "Too short"},
        )

    text = bot.send_message.call_args[0][1]
    assert "REJECTED" in text or "ОТКЛОНЕНО" in text


@pytest.mark.asyncio
async def test_notify_timeout_sends_new():
    bot = _mock_bot()
    with patch("bot.services.notifier.config", admin_chat_id=-100):
        await notify_timeout(bot, 1, "Group", 10, "alice", "Alice")

    bot.send_message.assert_called_once()
    bot.edit_message_text.assert_not_called()


@pytest.mark.asyncio
async def test_notify_timeout_edits_existing():
    bot = _mock_bot()
    with patch("bot.services.notifier.config", admin_chat_id=-100):
        await notify_timeout(bot, 1, "Group", 10, "alice", "Alice", admin_message_id=77)

    bot.edit_message_text.assert_called_once()
    bot.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_notify_timeout_falls_back_on_edit_failure():
    bot = _mock_bot()
    bot.edit_message_text.side_effect = Exception("edit failed")
    with patch("bot.services.notifier.config", admin_chat_id=-100):
        await notify_timeout(bot, 1, "Group", 10, "alice", "Alice", admin_message_id=77)

    bot.send_message.assert_called_once()
