from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.types import Message

from bot.db import members
from bot.services import onboarding

log = logging.getLogger(__name__)
router = Router(name="message")


@router.message(F.text, F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
async def on_group_message(message: Message, bot: Bot) -> None:
    """Check if this message is a response to onboarding."""
    user = message.from_user
    if not user:
        return

    # Quick check: is this user pending onboarding?
    member = await members.get_member(message.chat.id, user.id)
    if not member or member.status not in ("joined", "prompt_sent"):
        return

    log.info(
        "Onboarding response from user_id=%d in chat_id=%d",
        user.id, message.chat.id,
    )
    await onboarding.handle_response(
        bot=bot,
        chat_id=message.chat.id,
        chat_title=message.chat.title,
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        text=message.text,
    )


@router.message(~F.text, F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
async def on_non_text_message(message: Message, bot: Bot) -> None:
    """Remind pending members to write text."""
    user = message.from_user
    if not user:
        return

    member = await members.get_member(message.chat.id, user.id)
    if not member or member.status not in ("joined", "prompt_sent"):
        return

    display = f"@{user.username}" if user.username else (user.first_name or str(user.id))
    await message.reply(f"{display}, пожалуйста, представьтесь текстом.")
