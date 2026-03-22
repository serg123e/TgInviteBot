from __future__ import annotations

import logging

from aiogram import Bot, Router
from aiogram.types import ChatMemberUpdated

from bot.services import onboarding

log = logging.getLogger(__name__)
router = Router(name="new_member")


@router.chat_member()
async def on_chat_member_update(event: ChatMemberUpdated, bot: Bot) -> None:
    """Handle new member joining via chat_member updates."""
    # Only process transitions to "member" or "restricted" (joined)
    old = event.old_chat_member
    new = event.new_chat_member

    if old.status in ("left", "kicked") and new.status in ("member", "restricted"):
        user = new.user
        log.info(
            "New member: user_id=%d username=%s chat_id=%d",
            user.id, user.username, event.chat.id,
        )
        await onboarding.handle_new_member(
            bot=bot,
            chat_id=event.chat.id,
            chat_title=event.chat.title,
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            is_bot=user.is_bot,
        )
