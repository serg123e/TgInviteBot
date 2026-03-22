from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.config import config

log = logging.getLogger(__name__)


def _user_display(username: str | None, first_name: str | None, user_id: int) -> str:
    if username:
        return f"@{username}"
    if first_name:
        return f"{first_name} (id: {user_id})"
    return f"id: {user_id}"


async def notify_new_member(
    bot: Bot,
    chat_id: int,
    chat_title: str | None,
    user_id: int,
    username: str | None,
    first_name: str | None,
) -> None:
    display = _user_display(username, first_name, user_id)
    text = (
        f"Новый участник в <b>{chat_title or chat_id}</b>\n"
        f"Пользователь: {display}\n"
        f"Статус: ожидает представления"
    )
    await bot.send_message(config.admin_chat_id, text, parse_mode="HTML")


async def notify_response(
    bot: Bot,
    chat_id: int,
    chat_title: str | None,
    user_id: int,
    username: str | None,
    first_name: str | None,
    response_text: str,
    ai_result: dict | None,
) -> None:
    display = _user_display(username, first_name, user_id)
    ai_valid = ai_result.get("valid", "?") if ai_result else "N/A"
    ai_reason = ai_result.get("reason", "") if ai_result else ""

    status_emoji = "OK" if ai_valid is True else ("REJECTED" if ai_valid is False else "?")

    text = (
        f"Представление в <b>{chat_title or chat_id}</b>\n"
        f"Пользователь: {display}\n"
        f"AI: {status_emoji} — {ai_reason}\n\n"
        f"<i>{response_text[:500]}</i>"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Одобрить",
                    callback_data=f"approve:{chat_id}:{user_id}",
                ),
                InlineKeyboardButton(
                    text="Удалить",
                    callback_data=f"remove:{chat_id}:{user_id}",
                ),
                InlineKeyboardButton(
                    text="Забанить",
                    callback_data=f"ban:{chat_id}:{user_id}",
                ),
            ]
        ]
    )

    await bot.send_message(
        config.admin_chat_id, text, parse_mode="HTML", reply_markup=keyboard
    )


async def notify_timeout(
    bot: Bot,
    chat_id: int,
    chat_title: str | None,
    user_id: int,
    username: str | None,
    first_name: str | None,
) -> None:
    display = _user_display(username, first_name, user_id)
    text = (
        f"Таймаут в <b>{chat_title or chat_id}</b>\n"
        f"Пользователь {display} не представился и был удалён."
    )
    await bot.send_message(config.admin_chat_id, text, parse_mode="HTML")
