from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from html import escape

from aiogram import Bot

from bot.db import events, members, settings
from bot.i18n import t
from bot.services import ai_validator, notifier
from bot.services.scheduler import cancel_removal, schedule_removal
from bot.status import Status
from bot.utils.template import render, user_display

log = logging.getLogger(__name__)


async def handle_new_member(
    bot: Bot,
    chat_id: int,
    chat_title: str | None,
    user_id: int,
    username: str | None,
    first_name: str | None,
    last_name: str | None,
    is_bot: bool,
) -> None:
    """Process a new member joining the group."""
    cfg = await settings.get_or_create(chat_id, chat_title)

    if not cfg.is_active:
        return

    if is_bot and cfg.ignore_bots:
        log.info("Ignoring bot user %d in chat %d", user_id, chat_id)
        return

    # Check whitelist
    existing = await members.get_member(chat_id, user_id)
    if existing and existing.is_whitelisted and cfg.whitelist_enabled:
        log.info("Whitelisted user %d rejoined chat %d", user_id, chat_id)
        await events.log_event("whitelist_skip", chat_id, user_id)
        return

    # Upsert member
    await members.upsert_member(chat_id, user_id, username, first_name, last_name)

    # Send welcome message
    display = escape(username) if username else (escape(first_name) if first_name else str(user_id))
    mention = f"@{display}" if username else display
    if "{user}" in cfg.welcome_text:
        welcome = render(cfg.welcome_text, timeout=cfg.timeout_minutes, user=mention)
    else:
        welcome = f"{mention}, {render(cfg.welcome_text, timeout=cfg.timeout_minutes)}"

    msg = await bot.send_message(chat_id, welcome)

    # Schedule removal
    schedule_removal(chat_id, user_id, cfg.timeout_minutes, bot)

    # Notify admin
    admin_msg_id = await notifier.notify_new_member(bot, chat_id, chat_title, user_id, username, first_name)

    # Update member with prompt info and admin message in a single call
    await members.update_status(
        chat_id, user_id, "prompt_sent",
        prompt_sent_at=datetime.now(timezone.utc),
        prompt_message_id=msg.message_id,
        **({"admin_message_id": admin_msg_id} if admin_msg_id else {}),
    )
    await events.log_event("new_member", chat_id, user_id, {"username": username})


async def handle_response(
    bot: Bot,
    chat_id: int,
    chat_title: str | None,
    user_id: int,
    username: str | None,
    first_name: str | None,
    text: str,
) -> None:
    """Process a member's introduction response."""
    cfg = await settings.get_or_create(chat_id, chat_title)
    member = await members.get_member(chat_id, user_id)

    if not member or member.status not in Status.RESPONDABLE:
        return

    # Check minimum length
    if len(text.strip()) < cfg.min_response_length:
        display = user_display(username, first_name, user_id)
        await bot.send_message(
            chat_id,
            t("{user}, message too short. Minimum {min_len} characters.",
              user=display, min_len=cfg.min_response_length),
        )
        return

    # Cancel the timeout
    cancel_removal(chat_id, user_id)

    # AI validation
    ai_result = None
    if cfg.ai_validation_enabled:
        ai_result = await ai_validator.validate_response(text)

    # Update member
    new_status = Status.APPROVED if (ai_result is None or ai_result.get("valid")) else Status.PENDING_RETRY
    await members.update_status(
        chat_id, user_id, new_status,
        response_text=text,
        responded_at=datetime.now(timezone.utc),
        ai_validation_result=ai_result,
    )

    if new_status == Status.APPROVED:
        await bot.send_message(chat_id, t("Thanks for the introduction! Welcome to the group."))
        await events.log_event("approved_auto", chat_id, user_id)
    else:
        # Re-schedule removal for pending_retry — give user time to try again
        schedule_removal(chat_id, user_id, cfg.timeout_minutes, bot)
        await events.log_event("pending_retry_ai", chat_id, user_id, ai_result)

    # Notify admin with response details
    await notifier.notify_response(
        bot, chat_id, chat_title, user_id, username, first_name, text, ai_result,
        admin_message_id=member.admin_message_id,
    )


async def handle_timeout(bot: Bot, chat_id: int, user_id: int) -> None:
    """Remove a member who didn't respond in time."""
    member = await members.get_member(chat_id, user_id)
    if not member or member.status not in Status.RESPONDABLE:
        return

    cfg = await settings.get_or_create(chat_id)

    try:
        if cfg.ban_on_remove:
            if cfg.ban_duration_hours is not None:
                until = datetime.now(timezone.utc) + timedelta(hours=cfg.ban_duration_hours)
                await bot.ban_chat_member(chat_id, user_id, until_date=until)
            else:
                await bot.ban_chat_member(chat_id, user_id)
        else:
            await bot.ban_chat_member(chat_id, user_id)
            await bot.unban_chat_member(chat_id, user_id)
    except Exception as e:
        log.error("Failed to remove user %d from chat %d: %s", user_id, chat_id, e)
        await members.update_status(chat_id, user_id, Status.ERROR, removal_reason=str(e))
        return

    reason = "timeout"
    await members.update_status(
        chat_id, user_id, Status.REMOVED_TIMEOUT,
        removed_at=datetime.now(timezone.utc),
        removal_reason=reason,
    )

    # Delete welcome prompt message
    if member.prompt_message_id:
        try:
            await bot.delete_message(chat_id, member.prompt_message_id)
        except Exception:
            pass

    await notifier.notify_timeout(
        bot, chat_id, cfg.chat_title, user_id, member.username, member.first_name,
        admin_message_id=member.admin_message_id,
    )
    await events.log_event("removed_timeout", chat_id, user_id, {"reason": reason})


async def approve_member(bot: Bot, chat_id: int, user_id: int) -> bool:
    """Manually approve a member."""
    member = await members.get_member(chat_id, user_id)
    if not member:
        return False

    cancel_removal(chat_id, user_id)
    await members.update_status(chat_id, user_id, Status.APPROVED)
    await events.log_event("approved_manual", chat_id, user_id)
    return True


async def remove_member(bot: Bot, chat_id: int, user_id: int, ban: bool = False) -> bool:
    """Manually remove (or ban) a member."""
    member = await members.get_member(chat_id, user_id)
    if not member:
        return False

    cancel_removal(chat_id, user_id)

    try:
        await bot.ban_chat_member(chat_id, user_id)
        if not ban:
            await bot.unban_chat_member(chat_id, user_id)
    except Exception as e:
        log.error("Failed to remove user %d from chat %d: %s", user_id, chat_id, e)
        return False

    status = Status.REMOVED_MANUAL
    reason = "manual_ban" if ban else "manual_remove"
    await members.update_status(
        chat_id, user_id, status,
        removed_at=datetime.now(timezone.utc),
        removal_reason=reason,
    )
    await events.log_event(reason, chat_id, user_id)
    return True


async def restore_timers(bot: Bot) -> int:
    """Restore pending timers after bot restart. Returns count of restored timers."""
    pending = await members.get_pending_members()
    count = 0
    now = datetime.now(timezone.utc)

    for member in pending:
        cfg = await settings.get_or_create(member.chat_id)
        joined = datetime.fromisoformat(member.joined_at).replace(tzinfo=timezone.utc)
        elapsed = (now - joined).total_seconds() / 60
        remaining = cfg.timeout_minutes - elapsed

        if remaining <= 0:
            # Already expired — remove immediately
            await handle_timeout(bot, member.chat_id, member.telegram_user_id)
        else:
            schedule_removal(member.chat_id, member.telegram_user_id, remaining, bot)
        count += 1

    log.info("Restored %d pending timers", count)
    return count
