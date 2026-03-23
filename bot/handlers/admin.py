from __future__ import annotations

import logging
from typing import Any

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.config import config
from bot.db import members, settings
from bot.i18n import t
from bot.services import onboarding
from bot.utils.template import user_display

log = logging.getLogger(__name__)
router = Router(name="admin")


# --- Inline button callbacks ---


@router.callback_query(F.data.startswith("approve:"))
async def on_approve_callback(callback: CallbackQuery, bot: Bot) -> None:
    if not callback.data or not isinstance(callback.message, Message):
        return
    if callback.message.chat.id != config.admin_chat_id:
        return
    parts = callback.data.split(":")
    try:
        chat_id, user_id = int(parts[1]), int(parts[2])
    except (ValueError, IndexError):
        await callback.answer("Invalid callback data")
        return

    ok = await onboarding.approve_member(bot, chat_id, user_id)
    if ok:
        await callback.answer(t("User approved"))
        await callback.message.edit_text(
            (callback.message.text or "") + "\n\n" + t("--- APPROVED ---"),
            parse_mode="HTML",
        )
    else:
        await callback.answer(t("User not found"))


@router.callback_query(F.data.startswith("remove:"))
async def on_remove_callback(callback: CallbackQuery, bot: Bot) -> None:
    if not callback.data or not isinstance(callback.message, Message):
        return
    if callback.message.chat.id != config.admin_chat_id:
        return
    parts = callback.data.split(":")
    try:
        chat_id, user_id = int(parts[1]), int(parts[2])
    except (ValueError, IndexError):
        await callback.answer("Invalid callback data")
        return

    ok = await onboarding.remove_member(bot, chat_id, user_id, ban=False)
    if ok:
        await callback.answer(t("User removed"))
        await callback.message.edit_text(
            (callback.message.text or "") + "\n\n" + t("--- REMOVED ---"),
            parse_mode="HTML",
        )
    else:
        await callback.answer(t("Could not remove"))


@router.callback_query(F.data.startswith("ban:"))
async def on_ban_callback(callback: CallbackQuery, bot: Bot) -> None:
    if not callback.data or not isinstance(callback.message, Message):
        return
    if callback.message.chat.id != config.admin_chat_id:
        return
    parts = callback.data.split(":")
    try:
        chat_id, user_id = int(parts[1]), int(parts[2])
    except (ValueError, IndexError):
        await callback.answer("Invalid callback data")
        return

    ok = await onboarding.remove_member(bot, chat_id, user_id, ban=True)
    if ok:
        await callback.answer(t("User banned"))
        await callback.message.edit_text(
            (callback.message.text or "") + "\n\n" + t("--- BANNED ---"),
            parse_mode="HTML",
        )
    else:
        await callback.answer(t("Could not ban"))


# --- Admin commands (only work in admin chat) ---


@router.message(Command("pending"), F.chat.id == config.admin_chat_id)
async def cmd_pending(message: Message, bot: Bot) -> None:
    """Show pending members across all chats or for a specific chat."""
    if not message.text:
        return
    args = message.text.split(maxsplit=1)
    try:
        chat_id = int(args[1]) if len(args) > 1 else None
    except ValueError:
        await message.reply("Invalid chat_id. Usage: /pending [chat_id]")
        return

    pending = await members.get_pending_members(chat_id)
    if not pending:
        await message.reply(t("No pending members."))
        return

    lines = []
    for m in pending[:50]:
        display = user_display(m.username, m.first_name, m.telegram_user_id)
        lines.append(f"  {display} — chat {m.chat_id} — {m.status} — {m.joined_at}")

    text = t("Pending: {count}", count=len(pending)) + "\n" + "\n".join(lines)
    await message.reply(text[:4000])


@router.message(Command("config"), F.chat.id == config.admin_chat_id)
async def cmd_config(message: Message, bot: Bot) -> None:
    """/config <chat_id> [key=value ...]"""
    if not message.text:
        return
    args = message.text.split()
    if len(args) < 2:
        await message.reply(
            "Usage: /config <chat_id> [key=value ...]\n\n"
            "Keys: timeout_minutes, min_response_length, ai_validation_enabled, "
            "ban_on_remove, ignore_bots, is_active, welcome_text"
        )
        return

    try:
        chat_id = int(args[1])
    except ValueError:
        await message.reply("Invalid chat_id. Usage: /config <chat_id> [key=value ...]")
        return

    if len(args) == 2:
        # Show current config
        cfg = await settings.get_or_create(chat_id)
        text = (
            t("Settings for chat {chat_id}:", chat_id=chat_id) + "\n"
            f"  welcome_text: {cfg.welcome_text[:100]}\n"
            f"  timeout_minutes: {cfg.timeout_minutes}\n"
            f"  min_response_length: {cfg.min_response_length}\n"
            f"  ai_validation_enabled: {cfg.ai_validation_enabled}\n"
            f"  ban_on_remove: {cfg.ban_on_remove}\n"
            f"  ignore_bots: {cfg.ignore_bots}\n"
            f"  is_active: {cfg.is_active}"
        )
        await message.reply(text)
        return

    # Parse key=value pairs
    updates: dict[str, Any] = {}
    bool_keys = {"ai_validation_enabled", "ban_on_remove", "ignore_bots", "is_active"}
    int_keys = {"timeout_minutes", "min_response_length"}
    str_keys = {"welcome_text"}

    for arg in args[2:]:
        if "=" not in arg:
            continue
        key, value = arg.split("=", 1)
        if key in bool_keys:
            updates[key] = value.lower() in ("true", "1", "yes")
        elif key in int_keys:
            try:
                updates[key] = int(value)
            except ValueError:
                await message.reply(t("Invalid integer for {name}: {value}", name=key, value=value))
                return
        elif key in str_keys:
            updates[key] = value
        else:
            await message.reply(t("Unknown key: {name}", name=key))
            return

    result = await settings.update(chat_id, **updates)
    if result:
        await message.reply(t("Settings for chat {chat_id} updated.", chat_id=chat_id))
    else:
        await message.reply(t("Chat not found."))
