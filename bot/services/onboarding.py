from __future__ import annotations

import logging
from datetime import datetime, timezone

from aiogram import Bot

from bot.db import members, settings
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

    # Check whitelist (always on — approved members are auto-whitelisted)
    existing = await members.get_member(chat_id, user_id)
    if existing and existing.is_whitelisted:
        log.info("Whitelisted user %d rejoined chat %d", user_id, chat_id)
        return

    # Upsert member
    await members.upsert_member(chat_id, user_id, username, first_name, last_name)

    # Send welcome message
    mention = user_display(username, first_name, user_id)
    welcome = render(cfg.welcome_text, timeout=cfg.timeout_minutes, user=mention)

    try:
        msg = await bot.send_message(chat_id, welcome)
        log.info("Sent welcome to user %d in chat %d (msg_id=%d)", user_id, chat_id, msg.message_id)
    except Exception as e:
        log.error("Failed to send welcome to chat %d: %s", chat_id, e)
        return

    # Schedule removal
    schedule_removal(chat_id, user_id, cfg.timeout_minutes, bot)

    # Notify admin
    try:
        admin_msg_id = await notifier.notify_new_member(bot, chat_id, chat_title, user_id, username, first_name)
    except Exception as e:
        log.error("Failed to notify admin: %s", e)
        admin_msg_id = None

    # Update member with prompt info and admin message in a single call
    await members.update_status(
        chat_id, user_id, "prompt_sent",
        prompt_sent_at=datetime.now(timezone.utc),
        prompt_message_id=msg.message_id,
        **({"admin_message_id": admin_msg_id} if admin_msg_id else {}),
    )


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
        # Auto-whitelist approved members
        await members.set_whitelisted(chat_id, user_id, True)
    else:
        # Re-schedule removal for pending_retry — give user time to try again
        schedule_removal(chat_id, user_id, cfg.timeout_minutes, bot)

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
            await bot.ban_chat_member(chat_id, user_id)
        else:
            await bot.ban_chat_member(chat_id, user_id)
            await bot.unban_chat_member(chat_id, user_id)
    except Exception as e:
        log.error("Failed to remove user %d from chat %d: %s", user_id, chat_id, e)
        await members.update_status(chat_id, user_id, Status.ERROR, removal_reason=str(e))
        try:
            await notifier.notify_error(
                bot, chat_id, cfg.chat_title, user_id, member.username, member.first_name,
                error=str(e), admin_message_id=member.admin_message_id,
            )
        except Exception as notify_err:
            log.error("Failed to notify admin about error: %s", notify_err)
        return

    await members.update_status(
        chat_id, user_id, Status.REMOVED_TIMEOUT,
        removed_at=datetime.now(timezone.utc),
        removal_reason="timeout",
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


async def approve_member(bot: Bot, chat_id: int, user_id: int) -> bool:
    """Manually approve a member."""
    member = await members.get_member(chat_id, user_id)
    if not member:
        return False

    cancel_removal(chat_id, user_id)
    await members.update_status(chat_id, user_id, Status.APPROVED)
    # Auto-whitelist approved members
    await members.set_whitelisted(chat_id, user_id, True)
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

    await members.update_status(
        chat_id, user_id, Status.REMOVED_MANUAL,
        removed_at=datetime.now(timezone.utc),
        removal_reason="manual_ban" if ban else "manual_remove",
    )
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
