"""Tests for onboarding service — requires DB mocking."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.services.onboarding import handle_new_member, handle_response


@pytest.mark.asyncio
async def test_handle_new_member_ignores_bots():
    """Bots should be ignored when ignore_bots is True."""
    mock_cfg = MagicMock()
    mock_cfg.is_active = True
    mock_cfg.ignore_bots = True

    bot = AsyncMock()

    with patch("bot.services.onboarding.settings.get_or_create", return_value=mock_cfg):
        await handle_new_member(
            bot=bot,
            chat_id=-100123,
            chat_title="Test",
            user_id=111,
            username="test_bot",
            first_name="Bot",
            last_name=None,
            is_bot=True,
        )
        # Bot should NOT have sent any message
        bot.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_handle_response_ai_disabled_auto_approves():
    """When AI validation is disabled, valid responses are auto-approved."""
    bot = AsyncMock()
    mock_cfg = MagicMock()
    mock_cfg.ai_validation_enabled = False
    mock_cfg.min_response_length = 5

    mock_member = MagicMock()
    mock_member.status = "prompt_sent"
    mock_member.admin_message_id = 100

    with patch("bot.services.onboarding.settings.get_or_create", return_value=mock_cfg), \
         patch("bot.services.onboarding.members.get_member", return_value=mock_member), \
         patch("bot.services.onboarding.cancel_removal"), \
         patch("bot.services.onboarding.members.update_status", new_callable=AsyncMock) as upd, \
         patch("bot.services.onboarding.notifier.notify_response", new_callable=AsyncMock), \
         patch("bot.services.onboarding.events.log_event", new_callable=AsyncMock):

        await handle_response(
            bot=bot, chat_id=-100123, chat_title="Test",
            user_id=1, username="alice", first_name="Alice",
            text="Hi, I'm Alice, a developer from Moscow.",
        )

    # Should be approved (ai_result is None → approved)
    status_arg = upd.call_args[0][2]
    assert status_arg == "approved"


@pytest.mark.asyncio
async def test_handle_new_member_whitelisted():
    """Whitelisted users should be skipped."""
    mock_cfg = MagicMock()
    mock_cfg.is_active = True
    mock_cfg.ignore_bots = False
    mock_cfg.whitelist_enabled = True

    mock_member = MagicMock()
    mock_member.is_whitelisted = True

    bot = AsyncMock()

    with patch("bot.services.onboarding.settings.get_or_create", return_value=mock_cfg), \
         patch("bot.services.onboarding.members.get_member", return_value=mock_member), \
         patch("bot.services.onboarding.events.log_event", new_callable=AsyncMock):
        await handle_new_member(
            bot=bot,
            chat_id=-100123,
            chat_title="Test",
            user_id=222,
            username="user",
            first_name="User",
            last_name=None,
            is_bot=False,
        )
        bot.send_message.assert_not_called()
