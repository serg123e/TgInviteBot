from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.config import config
from bot.db import members, settings
from bot.services import onboarding

log = logging.getLogger(__name__)
router = Router(name="admin")


def _is_admin_chat(chat_id: int) -> bool:
    return chat_id == config.admin_chat_id


# --- Inline button callbacks ---


@router.callback_query(F.data.startswith("approve:"))
async def on_approve_callback(callback: CallbackQuery, bot: Bot) -> None:
    parts = callback.data.split(":")
    chat_id, user_id = int(parts[1]), int(parts[2])

    ok = await onboarding.approve_member(bot, chat_id, user_id)
    if ok:
        await callback.answer("Пользователь одобрен")
        await callback.message.edit_text(
            callback.message.text + "\n\n--- ОДОБРЕН ---", parse_mode="HTML"
        )
    else:
        await callback.answer("Пользователь не найден")


@router.callback_query(F.data.startswith("remove:"))
async def on_remove_callback(callback: CallbackQuery, bot: Bot) -> None:
    parts = callback.data.split(":")
    chat_id, user_id = int(parts[1]), int(parts[2])

    ok = await onboarding.remove_member(bot, chat_id, user_id, ban=False)
    if ok:
        await callback.answer("Пользователь удалён")
        await callback.message.edit_text(
            callback.message.text + "\n\n--- УДАЛЁН ---", parse_mode="HTML"
        )
    else:
        await callback.answer("Не удалось удалить")


@router.callback_query(F.data.startswith("ban:"))
async def on_ban_callback(callback: CallbackQuery, bot: Bot) -> None:
    parts = callback.data.split(":")
    chat_id, user_id = int(parts[1]), int(parts[2])

    ok = await onboarding.remove_member(bot, chat_id, user_id, ban=True)
    if ok:
        await callback.answer("Пользователь забанен")
        await callback.message.edit_text(
            callback.message.text + "\n\n--- ЗАБАНЕН ---", parse_mode="HTML"
        )
    else:
        await callback.answer("Не удалось забанить")


# --- Admin commands (only work in admin chat) ---


@router.message(Command("pending"), F.chat.id == config.admin_chat_id)
async def cmd_pending(message: Message, bot: Bot) -> None:
    """Show pending members across all chats or for a specific chat."""
    args = message.text.split(maxsplit=1)
    chat_id = int(args[1]) if len(args) > 1 else None

    pending = await members.get_pending_members(chat_id)
    if not pending:
        await message.reply("Нет ожидающих участников.")
        return

    lines = []
    for m in pending[:50]:
        display = f"@{m.username}" if m.username else (m.first_name or str(m.telegram_user_id))
        lines.append(f"  {display} — chat {m.chat_id} — {m.status} — {m.joined_at:%H:%M %d.%m}")

    text = f"Ожидающих: {len(pending)}\n" + "\n".join(lines)
    await message.reply(text[:4000])


@router.message(Command("approve"), F.chat.id == config.admin_chat_id)
async def cmd_approve(message: Message, bot: Bot) -> None:
    """/approve <chat_id> <user_id|@username>"""
    args = message.text.split()
    if len(args) < 3:
        await message.reply("Использование: /approve <chat_id> <user_id>")
        return

    chat_id = int(args[1])
    user_id = int(args[2])
    ok = await onboarding.approve_member(bot, chat_id, user_id)
    await message.reply("Одобрен." if ok else "Не найден.")


@router.message(Command("remove"), F.chat.id == config.admin_chat_id)
async def cmd_remove(message: Message, bot: Bot) -> None:
    """/remove <chat_id> <user_id>"""
    args = message.text.split()
    if len(args) < 3:
        await message.reply("Использование: /remove <chat_id> <user_id>")
        return

    chat_id = int(args[1])
    user_id = int(args[2])
    ok = await onboarding.remove_member(bot, chat_id, user_id)
    await message.reply("Удалён." if ok else "Не удалось удалить.")


@router.message(Command("ban"), F.chat.id == config.admin_chat_id)
async def cmd_ban(message: Message, bot: Bot) -> None:
    """/ban <chat_id> <user_id>"""
    args = message.text.split()
    if len(args) < 3:
        await message.reply("Использование: /ban <chat_id> <user_id>")
        return

    chat_id = int(args[1])
    user_id = int(args[2])
    ok = await onboarding.remove_member(bot, chat_id, user_id, ban=True)
    await message.reply("Забанен." if ok else "Не удалось забанить.")


@router.message(Command("whitelist"), F.chat.id == config.admin_chat_id)
async def cmd_whitelist(message: Message, bot: Bot) -> None:
    """/whitelist <chat_id> <user_id>"""
    args = message.text.split()
    if len(args) < 3:
        await message.reply("Использование: /whitelist <chat_id> <user_id>")
        return

    chat_id = int(args[1])
    user_id = int(args[2])
    member = await members.set_whitelisted(chat_id, user_id, True)
    if member:
        await onboarding.approve_member(bot, chat_id, user_id)
        await message.reply(f"Пользователь {user_id} добавлен в whitelist и одобрен.")
    else:
        await message.reply("Пользователь не найден.")


@router.message(Command("status"), F.chat.id == config.admin_chat_id)
async def cmd_status(message: Message, bot: Bot) -> None:
    """/status <chat_id> <user_id>"""
    args = message.text.split()
    if len(args) < 3:
        await message.reply("Использование: /status <chat_id> <user_id>")
        return

    chat_id = int(args[1])
    user_id = int(args[2])
    member = await members.get_member(chat_id, user_id)
    if not member:
        await message.reply("Пользователь не найден.")
        return

    display = f"@{member.username}" if member.username else (member.first_name or str(user_id))
    text = (
        f"Пользователь: {display}\n"
        f"Чат: {chat_id}\n"
        f"Статус: {member.status}\n"
        f"Вступил: {member.joined_at:%Y-%m-%d %H:%M}\n"
        f"Whitelisted: {'да' if member.is_whitelisted else 'нет'}\n"
    )
    if member.response_text:
        text += f"Ответ: {member.response_text[:200]}\n"
    if member.ai_validation_result:
        text += f"AI: {member.ai_validation_result}\n"

    await message.reply(text)


@router.message(Command("config"), F.chat.id == config.admin_chat_id)
async def cmd_config(message: Message, bot: Bot) -> None:
    """/config <chat_id> [key=value ...]"""
    args = message.text.split()
    if len(args) < 2:
        await message.reply(
            "Использование: /config <chat_id> [key=value ...]\n\n"
            "Ключи: timeout_minutes, min_response_length, ai_validation_enabled, "
            "ban_on_remove, ban_duration_hours, whitelist_enabled, ignore_bots, "
            "is_active, welcome_text"
        )
        return

    chat_id = int(args[1])

    if len(args) == 2:
        # Show current config
        cfg = await settings.get_or_create(chat_id)
        text = (
            f"Настройки чата {chat_id}:\n"
            f"  welcome_text: {cfg.welcome_text[:100]}\n"
            f"  timeout_minutes: {cfg.timeout_minutes}\n"
            f"  min_response_length: {cfg.min_response_length}\n"
            f"  ai_validation_enabled: {cfg.ai_validation_enabled}\n"
            f"  ban_on_remove: {cfg.ban_on_remove}\n"
            f"  ban_duration_hours: {cfg.ban_duration_hours}\n"
            f"  whitelist_enabled: {cfg.whitelist_enabled}\n"
            f"  ignore_bots: {cfg.ignore_bots}\n"
            f"  is_active: {cfg.is_active}"
        )
        await message.reply(text)
        return

    # Parse key=value pairs
    updates = {}
    bool_keys = {"ai_validation_enabled", "ban_on_remove", "whitelist_enabled", "ignore_bots", "is_active"}
    int_keys = {"timeout_minutes", "min_response_length", "ban_duration_hours"}
    str_keys = {"welcome_text"}

    for arg in args[2:]:
        if "=" not in arg:
            continue
        key, value = arg.split("=", 1)
        if key in bool_keys:
            updates[key] = value.lower() in ("true", "1", "yes")
        elif key in int_keys:
            updates[key] = int(value) if value.lower() != "null" else None
        elif key in str_keys:
            updates[key] = value
        else:
            await message.reply(f"Неизвестный ключ: {key}")
            return

    cfg = await settings.update(chat_id, **updates)
    if cfg:
        await message.reply(f"Настройки чата {chat_id} обновлены.")
    else:
        await message.reply("Чат не найден.")
