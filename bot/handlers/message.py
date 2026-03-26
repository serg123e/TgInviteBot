from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.enums import ChatType, ContentType
from aiogram.filters import Command
from aiogram.types import Message

from bot.db import members
from bot.i18n import t
from bot.services import onboarding
from bot.status import Status
from bot.utils.template import user_display

MEDIA_CONTENT_TYPES = {
    ContentType.PHOTO, ContentType.VIDEO, ContentType.AUDIO,
    ContentType.VOICE, ContentType.DOCUMENT, ContentType.STICKER,
    ContentType.ANIMATION, ContentType.VIDEO_NOTE,
}

log = logging.getLogger(__name__)
router = Router(name="message")


@router.message(Command("chatid"))
async def on_chatid_command(message: Message) -> None:
    """Reply with setup instructions showing the current chat's ID."""
    from bot.config import config

    if config.admin_chat_id:
        return
    await message.reply(
        f"Set this in your <code>.env</code> file and restart the bot:\n\n"
        f"<code>ADMIN_CHAT_ID={message.chat.id}</code>"
    )


@router.message(F.text, F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
async def on_group_message(message: Message, bot: Bot) -> None:
    """Check if this message is a response to onboarding."""
    user = message.from_user
    if not user:
        return

    # Quick check: is this user pending onboarding?
    member = await members.get_member(message.chat.id, user.id)
    if not member or member.status not in Status.RESPONDABLE:
        return

    log.info(
        "Onboarding response from user_id=%d in chat_id=%d",
        user.id, message.chat.id,
    )
    if not message.text:
        return
    await onboarding.handle_response(
        bot=bot,
        chat_id=message.chat.id,
        chat_title=message.chat.title,
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        text=message.text,
    )


@router.message(F.content_type.in_(MEDIA_CONTENT_TYPES), F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
async def on_non_text_message(message: Message, bot: Bot) -> None:
    """Handle media from pending members: use caption as intro, or remind to write text."""
    user = message.from_user
    if not user:
        return

    member = await members.get_member(message.chat.id, user.id)
    if not member or member.status not in Status.RESPONDABLE:
        return

    # If media has a caption, treat it as the introduction text
    if message.caption:
        log.info(
            "Onboarding response (caption) from user_id=%d in chat_id=%d",
            user.id, message.chat.id,
        )
        await onboarding.handle_response(
            bot=bot,
            chat_id=message.chat.id,
            chat_title=message.chat.title,
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            text=message.caption,
        )
        return

    await message.reply(
        t("{user}, please introduce yourself with text.", user=user_display(user.username, user.first_name, user.id))
    )
