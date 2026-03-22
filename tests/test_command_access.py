"""Tests that commands are restricted to the correct chats."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.handlers.admin import on_approve_callback
from bot.handlers.message import on_chatid_command


@pytest.mark.asyncio
async def test_chatid_works_when_admin_not_configured():
    """/chatid replies when ADMIN_CHAT_ID is 0 (not configured)."""
    message = AsyncMock()
    message.chat.id = -100999

    with patch("bot.config.config", MagicMock(admin_chat_id=0)):
        await on_chatid_command(message)

    message.reply.assert_called_once()
    reply_text = str(message.reply.call_args)
    assert "ADMIN_CHAT_ID=-100999" in reply_text


@pytest.mark.asyncio
async def test_chatid_silent_when_admin_configured():
    """/chatid does nothing after ADMIN_CHAT_ID is set."""
    message = AsyncMock()
    message.chat.id = -100999

    with patch("bot.config.config", MagicMock(admin_chat_id=-100888)):
        await on_chatid_command(message)

    message.reply.assert_not_called()


@pytest.mark.asyncio
async def test_callback_rejected_outside_admin_chat():
    """Approve callback is ignored if triggered outside the admin chat."""
    callback = AsyncMock()
    callback.data = "approve:100:1"
    msg = MagicMock()
    msg.chat.id = -100999  # not the admin chat
    callback.message = msg
    bot = AsyncMock()

    with patch("bot.handlers.admin.config", MagicMock(admin_chat_id=-100888)):
        await on_approve_callback(callback, bot)

    callback.answer.assert_not_called()


@pytest.mark.asyncio
async def test_callback_works_in_admin_chat():
    """Approve callback works when triggered in the admin chat."""
    callback = AsyncMock()
    callback.data = "approve:100:1"
    msg = AsyncMock()
    msg.chat.id = -100888
    msg.text = "Some notification"
    callback.message = msg
    bot = AsyncMock()

    with patch("bot.handlers.admin.config", MagicMock(admin_chat_id=-100888)), \
         patch("bot.handlers.admin.onboarding.approve_member", return_value=True), \
         patch("bot.handlers.admin.isinstance", return_value=True, create=True):
        await on_approve_callback(callback, bot)

    callback.answer.assert_called_once()
