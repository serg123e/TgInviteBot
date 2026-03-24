from __future__ import annotations

import logging
from html import escape

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.config import config
from bot.i18n import t
from bot.utils.template import user_display

log = logging.getLogger(__name__)


async def notify_new_member(
    bot: Bot,
    chat_id: int,
    chat_title: str | None,
    user_id: int,
    username: str | None,
    first_name: str | None,
) -> int | None:
    display = user_display(username, first_name, user_id)
    text = t(
        "New member in <b>{chat}</b>\nUser: {user}\nStatus: awaiting introduction",
        chat=escape(str(chat_title or chat_id)), user=display,
    )
    msg = await bot.send_message(config.admin_chat_id, text, parse_mode="HTML")
    return msg.message_id


async def notify_response(
    bot: Bot,
    chat_id: int,
    chat_title: str | None,
    user_id: int,
    username: str | None,
    first_name: str | None,
    response_text: str,
    ai_result: dict | None,
    admin_message_id: int | None = None,
) -> None:
    display = user_display(username, first_name, user_id)
    ai_valid = ai_result.get("valid", "?") if ai_result else "N/A"
    ai_reason = ai_result.get("reason", "") if ai_result else ""

    status_emoji = "OK" if ai_valid is True else ("REJECTED" if ai_valid is False else "?")

    text = t(
        "#Introduction {user} in <b>{chat}</b>\n\n<i>{intro}</i>\n\nAI: {status} — {reason}",
        user=display, chat=escape(str(chat_title or chat_id)),
        intro=escape(response_text[:500]), status=status_emoji, reason=escape(ai_reason),
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("Approve"),
                    callback_data=f"approve:{chat_id}:{user_id}",
                ),
                InlineKeyboardButton(
                    text=t("Remove"),
                    callback_data=f"remove:{chat_id}:{user_id}",
                ),
                InlineKeyboardButton(
                    text=t("Ban"),
                    callback_data=f"ban:{chat_id}:{user_id}",
                ),
            ]
        ]
    )

    if admin_message_id:
        try:
            await bot.edit_message_text(
                text, config.admin_chat_id, admin_message_id,  # type: ignore[arg-type]
                parse_mode="HTML", reply_markup=keyboard,
            )
            return
        except Exception as e:
            log.warning("Failed to edit admin message %d, sending new: %s", admin_message_id, e)
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
    admin_message_id: int | None = None,
) -> None:
    display = user_display(username, first_name, user_id)
    text = t(
        "#Timeout {user} in <b>{chat}</b>\nDid not introduce and was removed.",
        user=display, chat=escape(str(chat_title or chat_id)),
    )
    if admin_message_id:
        try:
            await bot.edit_message_text(
                text, config.admin_chat_id, admin_message_id,  # type: ignore[arg-type]
                parse_mode="HTML",
            )
            return
        except Exception as e:
            log.warning("Failed to edit admin message %d, sending new: %s", admin_message_id, e)
    await bot.send_message(config.admin_chat_id, text, parse_mode="HTML")


async def notify_error(
    bot: Bot,
    chat_id: int,
    chat_title: str | None,
    user_id: int,
    username: str | None,
    first_name: str | None,
    error: str,
    admin_message_id: int | None = None,
) -> None:
    display = user_display(username, first_name, user_id)
    text = t(
        "#Error {user} in <b>{chat}</b>\n{error}",
        user=display, chat=escape(str(chat_title or chat_id)), error=escape(error),
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("Approve"),
                    callback_data=f"approve:{chat_id}:{user_id}",
                ),
                InlineKeyboardButton(
                    text=t("Remove"),
                    callback_data=f"remove:{chat_id}:{user_id}",
                ),
            ]
        ]
    )
    if admin_message_id:
        try:
            await bot.edit_message_text(
                text, config.admin_chat_id, admin_message_id,  # type: ignore[arg-type]
                parse_mode="HTML", reply_markup=keyboard,
            )
            return
        except Exception as e:
            log.warning("Failed to edit admin message %d, sending new: %s", admin_message_id, e)
    await bot.send_message(
        config.admin_chat_id, text, parse_mode="HTML", reply_markup=keyboard
    )
