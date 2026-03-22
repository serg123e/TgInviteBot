from __future__ import annotations

import logging
from datetime import datetime, timezone

from aiogram import Bot, Router
from aiogram.types import ChatMemberUpdated

from bot.db import events, members
from bot.services.scheduler import cancel_removal
from bot.status import Status

log = logging.getLogger(__name__)
router = Router(name="member_left")


@router.chat_member()
async def on_member_left(event: ChatMemberUpdated, bot: Bot) -> None:
    """Handle member leaving the group."""
    old = event.old_chat_member
    new = event.new_chat_member

    if old.status in ("member", "restricted") and new.status in ("left", "kicked"):
        user = new.user

        member = await members.get_member(event.chat.id, user.id)
        if not member:
            return

        # Only update if still in an active onboarding status
        if member.status in Status.RESPONDABLE:
            cancel_removal(event.chat.id, user.id)
            await members.update_status(
                event.chat.id, user.id, Status.LEFT,
                removed_at=datetime.now(timezone.utc),
                removal_reason="left_voluntarily",
            )
            await events.log_event("member_left", event.chat.id, user.id)
            log.info("Member %d left chat %d", user.id, event.chat.id)
