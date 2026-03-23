"""Tests for onboarding service: handle_timeout, approve_member, remove_member, restore_timers."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.services.onboarding import (
    approve_member,
    handle_timeout,
    remove_member,
    restore_timers,
)

CHAT_ID = -100999


def _make_cfg(**overrides):
    cfg = MagicMock()
    cfg.ban_on_remove = False
    cfg.chat_title = "Test Group"
    cfg.timeout_minutes = 15
    for k, v in overrides.items():
        setattr(cfg, k, v)
    return cfg


def _make_member(status="prompt_sent", **overrides):
    m = MagicMock()
    m.chat_id = CHAT_ID
    m.telegram_user_id = 1
    m.status = status
    m.username = "alice"
    m.first_name = "Alice"
    m.prompt_message_id = 42
    m.admin_message_id = 100
    m.joined_at = "2025-01-01T00:00:00"
    for k, v in overrides.items():
        setattr(m, k, v)
    return m


# --- handle_timeout ---


@pytest.mark.asyncio
async def test_handle_timeout_kick():
    """Timeout with ban_on_remove=False → ban + unban (kick)."""
    bot = AsyncMock()
    member = _make_member()
    cfg = _make_cfg(ban_on_remove=False)

    with patch("bot.services.onboarding.members.get_member", return_value=member), \
         patch("bot.services.onboarding.settings.get_or_create", return_value=cfg), \
         patch("bot.services.onboarding.members.update_status", new_callable=AsyncMock) as upd, \
         patch("bot.services.onboarding.notifier.notify_timeout", new_callable=AsyncMock):

        await handle_timeout(bot, CHAT_ID, 1)

    bot.ban_chat_member.assert_called_once_with(CHAT_ID, 1)
    bot.unban_chat_member.assert_called_once_with(CHAT_ID, 1)
    upd.assert_called()
    status_arg = upd.call_args_list[-1][0][2]
    assert "removed" in status_arg


@pytest.mark.asyncio
async def test_handle_timeout_ban():
    """Timeout with ban_on_remove=True → ban only, no unban."""
    bot = AsyncMock()
    member = _make_member()
    cfg = _make_cfg(ban_on_remove=True)

    with patch("bot.services.onboarding.members.get_member", return_value=member), \
         patch("bot.services.onboarding.settings.get_or_create", return_value=cfg), \
         patch("bot.services.onboarding.members.update_status", new_callable=AsyncMock), \
         patch("bot.services.onboarding.notifier.notify_timeout", new_callable=AsyncMock):

        await handle_timeout(bot, CHAT_ID, 1)

    bot.ban_chat_member.assert_called_once()
    bot.unban_chat_member.assert_not_called()


@pytest.mark.asyncio
async def test_handle_timeout_skips_approved():
    """If member is already approved, timeout does nothing."""
    bot = AsyncMock()
    member = _make_member(status="approved")

    with patch("bot.services.onboarding.members.get_member", return_value=member):
        await handle_timeout(bot, CHAT_ID, 1)

    bot.ban_chat_member.assert_not_called()


@pytest.mark.asyncio
async def test_handle_timeout_member_not_found():
    bot = AsyncMock()

    with patch("bot.services.onboarding.members.get_member", return_value=None):
        await handle_timeout(bot, CHAT_ID, 1)

    bot.ban_chat_member.assert_not_called()


@pytest.mark.asyncio
async def test_handle_timeout_api_error():
    """If ban fails, status is set to 'error'."""
    bot = AsyncMock()
    bot.ban_chat_member.side_effect = Exception("API error")
    member = _make_member()
    cfg = _make_cfg()

    with patch("bot.services.onboarding.members.get_member", return_value=member), \
         patch("bot.services.onboarding.settings.get_or_create", return_value=cfg), \
         patch("bot.services.onboarding.members.update_status", new_callable=AsyncMock) as upd:

        await handle_timeout(bot, CHAT_ID, 1)

    upd.assert_called_once()
    assert upd.call_args[0][2] == "error"


@pytest.mark.asyncio
async def test_handle_timeout_deletes_prompt_message():
    bot = AsyncMock()
    member = _make_member(prompt_message_id=55)
    cfg = _make_cfg()

    with patch("bot.services.onboarding.members.get_member", return_value=member), \
         patch("bot.services.onboarding.settings.get_or_create", return_value=cfg), \
         patch("bot.services.onboarding.members.update_status", new_callable=AsyncMock), \
         patch("bot.services.onboarding.notifier.notify_timeout", new_callable=AsyncMock):

        await handle_timeout(bot, CHAT_ID, 1)

    bot.delete_message.assert_called_once_with(CHAT_ID, 55)


@pytest.mark.asyncio
async def test_handle_timeout_delete_message_failure_ignored():
    """Failure to delete prompt message should not break the flow."""
    bot = AsyncMock()
    bot.delete_message.side_effect = Exception("message not found")
    member = _make_member(prompt_message_id=55)
    cfg = _make_cfg()

    with patch("bot.services.onboarding.members.get_member", return_value=member), \
         patch("bot.services.onboarding.settings.get_or_create", return_value=cfg), \
         patch("bot.services.onboarding.members.update_status", new_callable=AsyncMock), \
         patch("bot.services.onboarding.notifier.notify_timeout", new_callable=AsyncMock) as nt:

        await handle_timeout(bot, CHAT_ID, 1)

    # Should still notify despite delete failure
    nt.assert_called_once()


@pytest.mark.asyncio
async def test_handle_timeout_passes_admin_message_id():
    """notify_timeout receives admin_message_id from the member."""
    bot = AsyncMock()
    member = _make_member(admin_message_id=777)
    cfg = _make_cfg()

    with patch("bot.services.onboarding.members.get_member", return_value=member), \
         patch("bot.services.onboarding.settings.get_or_create", return_value=cfg), \
         patch("bot.services.onboarding.members.update_status", new_callable=AsyncMock), \
         patch("bot.services.onboarding.notifier.notify_timeout", new_callable=AsyncMock) as nt:

        await handle_timeout(bot, CHAT_ID, 1)

    assert nt.call_args.kwargs["admin_message_id"] == 777


# --- approve_member ---


@pytest.mark.asyncio
async def test_approve_member_success():
    bot = AsyncMock()
    member = _make_member()

    with patch("bot.services.onboarding.members.get_member", return_value=member), \
         patch("bot.services.onboarding.cancel_removal") as cancel, \
         patch("bot.services.onboarding.members.update_status", new_callable=AsyncMock), \
         patch("bot.services.onboarding.members.set_whitelisted", new_callable=AsyncMock) as wl:

        result = await approve_member(bot, CHAT_ID, 1)

    assert result is True
    cancel.assert_called_once_with(CHAT_ID, 1)
    wl.assert_called_once_with(CHAT_ID, 1, True)


@pytest.mark.asyncio
async def test_approve_member_not_found():
    bot = AsyncMock()

    with patch("bot.services.onboarding.members.get_member", return_value=None):
        result = await approve_member(bot, CHAT_ID, 1)

    assert result is False


# --- remove_member ---


@pytest.mark.asyncio
async def test_remove_member_kick():
    bot = AsyncMock()
    member = _make_member()

    with patch("bot.services.onboarding.members.get_member", return_value=member), \
         patch("bot.services.onboarding.cancel_removal"), \
         patch("bot.services.onboarding.members.update_status", new_callable=AsyncMock):

        result = await remove_member(bot, CHAT_ID, 1, ban=False)

    assert result is True
    bot.ban_chat_member.assert_called_once()
    bot.unban_chat_member.assert_called_once()


@pytest.mark.asyncio
async def test_remove_member_ban():
    bot = AsyncMock()
    member = _make_member()

    with patch("bot.services.onboarding.members.get_member", return_value=member), \
         patch("bot.services.onboarding.cancel_removal"), \
         patch("bot.services.onboarding.members.update_status", new_callable=AsyncMock):

        result = await remove_member(bot, CHAT_ID, 1, ban=True)

    assert result is True
    bot.ban_chat_member.assert_called_once()
    bot.unban_chat_member.assert_not_called()


@pytest.mark.asyncio
async def test_remove_member_not_found():
    bot = AsyncMock()

    with patch("bot.services.onboarding.members.get_member", return_value=None):
        result = await remove_member(bot, CHAT_ID, 1)

    assert result is False


@pytest.mark.asyncio
async def test_remove_member_api_error():
    bot = AsyncMock()
    bot.ban_chat_member.side_effect = Exception("API error")
    member = _make_member()

    with patch("bot.services.onboarding.members.get_member", return_value=member), \
         patch("bot.services.onboarding.cancel_removal"):

        result = await remove_member(bot, CHAT_ID, 1)

    assert result is False


# --- restore_timers ---


@pytest.mark.asyncio
async def test_restore_timers_expired():
    """Expired members should be timed out immediately."""
    bot = AsyncMock()
    member = _make_member(joined_at="2020-01-01T00:00:00")
    cfg = _make_cfg(timeout_minutes=15)

    with patch("bot.services.onboarding.members.get_pending_members", return_value=[member]), \
         patch("bot.services.onboarding.settings.get_or_create", return_value=cfg), \
         patch("bot.services.onboarding.handle_timeout", new_callable=AsyncMock) as ht, \
         patch("bot.services.onboarding.schedule_removal"):

        count = await restore_timers(bot)

    assert count == 1
    ht.assert_called_once_with(bot, CHAT_ID, 1)


@pytest.mark.asyncio
async def test_restore_timers_still_pending():
    """Members with time remaining should be rescheduled."""
    bot = AsyncMock()
    from datetime import datetime, timedelta, timezone
    recent = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    member = _make_member(joined_at=recent)
    cfg = _make_cfg(timeout_minutes=30)

    with patch("bot.services.onboarding.members.get_pending_members", return_value=[member]), \
         patch("bot.services.onboarding.settings.get_or_create", return_value=cfg), \
         patch("bot.services.onboarding.handle_timeout", new_callable=AsyncMock) as ht, \
         patch("bot.services.onboarding.schedule_removal") as sched:

        count = await restore_timers(bot)

    assert count == 1
    ht.assert_not_called()
    sched.assert_called_once()


@pytest.mark.asyncio
async def test_restore_timers_empty():
    bot = AsyncMock()

    with patch("bot.services.onboarding.members.get_pending_members", return_value=[]):
        count = await restore_timers(bot)

    assert count == 0
