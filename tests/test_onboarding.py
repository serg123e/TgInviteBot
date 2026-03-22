"""Tests for onboarding service — requires DB mocking."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from bot.services.onboarding import handle_new_member


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
