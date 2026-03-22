from __future__ import annotations

import logging
from datetime import datetime, timezone

from aiogram import Bot

from bot.db import events, members, settings
from bot.services import ai_validator, notifier
from bot.services.scheduler import cancel_removal, schedule_removal
from bot.utils.template import render

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
    member = await members.upsert_member(chat_id, user_id, username, first_name, last_name)

    # Send welcome message
    welcome = render(cfg.welcome_text, timeout=cfg.timeout_minutes)
    if username:
        welcome = f"@{username}, {welcome}"
    elif first_name:
        welcome = f"{first_name}, {welcome}"

    msg = await bot.send_message(chat_id, welcome)

    # Update member with prompt info
    await members.update_status(
        chat_id, user_id, "prompt_sent",
        prompt_sent_at=datetime.now(timezone.utc),
        prompt_message_id=msg.message_id,
    )

    # Schedule removal
    schedule_removal(chat_id, user_id, cfg.timeout_minutes, bot)

    # Notify admin
    await notifier.notify_new_member(bot, chat_id, chat_title, user_id, username, first_name)
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

    if not member or member.status not in ("joined", "prompt_sent"):
        return

    # Check minimum length
    if len(text.strip()) < cfg.min_response_length:
        await bot.send_message(
            chat_id,
            f"@{username or first_name or user_id}, сообщение слишком короткое. "
            f"Минимум {cfg.min_response_length} символов.",
        )
        return

    # Cancel the timeout
    cancel_removal(chat_id, user_id)

    # AI validation
    ai_result = None
    if cfg.ai_validation_enabled:
        ai_result = await ai_validator.validate_response(text)

    # Update member
    new_status = "approved" if (ai_result is None or ai_result.get("valid")) else "rejected"
    await members.update_status(
        chat_id, user_id, new_status,
        response_text=text,
        responded_at=datetime.now(timezone.utc),
        ai_validation_result=ai_result,
    )

    if new_status == "approved":
        await bot.send_message(chat_id, f"Спасибо за представление! Добро пожаловать в группу.")
        await events.log_event("approved_auto", chat_id, user_id)
    else:
        # Re-schedule removal for rejected — give admins time to review
        schedule_removal(chat_id, user_id, cfg.timeout_minutes, bot)
        await events.log_event("rejected_ai", chat_id, user_id, ai_result)

    # Notify admin with response details
    await notifier.notify_response(
        bot, chat_id, chat_title, user_id, username, first_name, text, ai_result
    )


async def handle_timeout(bot: Bot, chat_id: int, user_id: int) -> None:
    """Remove a member who didn't respond in time."""
    member = await members.get_member(chat_id, user_id)
    if not member or member.status not in ("joined", "prompt_sent", "rejected"):
        return

    cfg = await settings.get_or_create(chat_id)

    try:
        if cfg.ban_on_remove:
            await bot.ban_chat_member(chat_id, user_id)
            if cfg.ban_duration_hours is not None:
                # Unban after duration to allow rejoin later
                pass  # Telegram auto-unbans with until_date
        else:
            await bot.ban_chat_member(chat_id, user_id)
            # Immediately unban to allow future rejoin (kick)
            await bot.unban_chat_member(chat_id, user_id, only_if_banned=True)
    except Exception as e:
        log.error("Failed to remove user %d from chat %d: %s", user_id, chat_id, e)
        await members.update_status(chat_id, user_id, "error", removal_reason=str(e))
        return

    reason = "no_response" if member.status in ("joined", "prompt_sent") else "rejected"
    new_status = f"removed_{reason}"
    await members.update_status(
        chat_id, user_id, new_status,
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
        bot, chat_id, cfg.chat_title, user_id, member.username, member.first_name
    )
    await events.log_event("removed_timeout", chat_id, user_id, {"reason": reason})


async def approve_member(bot: Bot, chat_id: int, user_id: int) -> bool:
    """Manually approve a member."""
    member = await members.get_member(chat_id, user_id)
    if not member:
        return False

    cancel_removal(chat_id, user_id)
    await members.update_status(chat_id, user_id, "approved")
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
            await bot.unban_chat_member(chat_id, user_id, only_if_banned=True)
    except Exception as e:
        log.error("Failed to remove user %d from chat %d: %s", user_id, chat_id, e)
        return False

    status = "removed_manual"
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
