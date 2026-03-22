"""Tests for message handlers — on_group_message and on_non_text_message."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.enums import ChatType, ContentType

from bot.handlers.message import on_group_message, on_non_text_message


def _make_message(chat_id=-100123, user_id=1, text="Hello", chat_type=ChatType.SUPERGROUP):
    msg = AsyncMock()
    msg.chat = MagicMock()
    msg.chat.id = chat_id
    msg.chat.title = "Test Group"
    msg.chat.type = chat_type
    msg.from_user = MagicMock()
    msg.from_user.id = user_id
    msg.from_user.username = "alice"
    msg.from_user.first_name = "Alice"
    msg.text = text
    msg.content_type = ContentType.TEXT
    return msg


@pytest.mark.asyncio
async def test_on_group_message_pending_member():
    """Pending member's text message triggers handle_response."""
    bot = AsyncMock()
    msg = _make_message(text="Hi, I'm Alice, a developer.")
    member = MagicMock()
    member.status = "prompt_sent"

    with patch("bot.handlers.message.members.get_member", return_value=member), \
         patch("bot.handlers.message.onboarding.handle_response", new_callable=AsyncMock) as hr:
        await on_group_message(msg, bot)

    hr.assert_called_once()


@pytest.mark.asyncio
async def test_on_group_message_non_pending_ignored():
    """Already approved members' messages are ignored."""
    bot = AsyncMock()
    msg = _make_message()
    member = MagicMock()
    member.status = "approved"

    with patch("bot.handlers.message.members.get_member", return_value=member), \
         patch("bot.handlers.message.onboarding.handle_response", new_callable=AsyncMock) as hr:
        await on_group_message(msg, bot)

    hr.assert_not_called()


@pytest.mark.asyncio
async def test_on_group_message_unknown_user_ignored():
    """Messages from users not in the DB are ignored."""
    bot = AsyncMock()
    msg = _make_message()

    with patch("bot.handlers.message.members.get_member", return_value=None), \
         patch("bot.handlers.message.onboarding.handle_response", new_callable=AsyncMock) as hr:
        await on_group_message(msg, bot)

    hr.assert_not_called()


@pytest.mark.asyncio
async def test_on_group_message_no_user():
    """Message with no from_user is ignored."""
    bot = AsyncMock()
    msg = _make_message()
    msg.from_user = None

    with patch("bot.handlers.message.members.get_member", new_callable=AsyncMock) as gm:
        await on_group_message(msg, bot)

    gm.assert_not_called()


@pytest.mark.asyncio
async def test_on_non_text_message_pending_member_gets_reminder():
    """Pending member sending media gets a text reminder."""
    bot = AsyncMock()
    msg = _make_message()
    msg.content_type = ContentType.PHOTO
    member = MagicMock()
    member.status = "prompt_sent"

    with patch("bot.handlers.message.members.get_member", return_value=member):
        await on_non_text_message(msg, bot)

    msg.reply.assert_called_once()


@pytest.mark.asyncio
async def test_on_non_text_message_approved_member_no_reminder():
    """Approved member sending media gets no reminder."""
    bot = AsyncMock()
    msg = _make_message()
    msg.content_type = ContentType.PHOTO
    member = MagicMock()
    member.status = "approved"

    with patch("bot.handlers.message.members.get_member", return_value=member):
        await on_non_text_message(msg, bot)

    msg.reply.assert_not_called()
