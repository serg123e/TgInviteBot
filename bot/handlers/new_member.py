from __future__ import annotations

import logging
import time

from aiogram import Bot, Router
from aiogram.types import ChatMemberUpdated, Message

from bot.services import onboarding

log = logging.getLogger(__name__)
router = Router(name="new_member")

# Dedup: Telegram may send both chat_member and message updates for the same join.
# Track recently processed joins to avoid double-processing.
_recent_joins: dict[tuple[int, int], float] = {}
_DEDUP_WINDOW = 5.0  # seconds


async def _process_join(bot: Bot, chat_id: int, chat_title: str | None, user) -> None:
    """Common logic for processing a new member join."""
    key = (chat_id, user.id)
    now = time.monotonic()

    # Skip if already processed within the dedup window
    if key in _recent_joins and (now - _recent_joins[key]) < _DEDUP_WINDOW:
        log.info("Dedup: skipping duplicate join for user %d in chat %d", user.id, chat_id)
        return
    _recent_joins[key] = now

    # Evict old entries
    cutoff = now - _DEDUP_WINDOW * 2
    for k in [k for k, t in _recent_joins.items() if t < cutoff]:
        del _recent_joins[k]

    log.info(
        "New member: user_id=%d username=%s chat_id=%d",
        user.id, user.username, chat_id,
    )
    await onboarding.handle_new_member(
        bot=bot,
        chat_id=chat_id,
        chat_title=chat_title,
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        is_bot=user.is_bot,
    )


@router.chat_member()
async def on_chat_member_update(event: ChatMemberUpdated, bot: Bot) -> None:
    """Handle new member joining via chat_member updates."""
    old = event.old_chat_member
    new = event.new_chat_member

    if old.status in ("left", "kicked") and new.status in ("member", "restricted"):
        await _process_join(bot, event.chat.id, event.chat.title, new.user)


@router.message(lambda msg: bool(msg.new_chat_members))
async def on_new_chat_members(message: Message, bot: Bot) -> None:
    """Handle new members via service message (new_chat_members)."""
    for user in message.new_chat_members:
        if user.id == bot.id:
            continue
        await _process_join(bot, message.chat.id, message.chat.title, user)
