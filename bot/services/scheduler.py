from __future__ import annotations

import asyncio
import logging

log = logging.getLogger(__name__)

_tasks: dict[tuple[int, int], asyncio.Task] = {}


def schedule_removal(chat_id: int, user_id: int, timeout_minutes: float, bot) -> str:
    """Schedule a member removal after timeout. Returns the job ID."""
    key = (chat_id, user_id)

    # Cancel existing task if any
    existing = _tasks.get(key)
    if existing and not existing.done():
        existing.cancel()

    async def _run() -> None:
        try:
            await asyncio.sleep(timeout_minutes * 60)
        except asyncio.CancelledError:
            return
        try:
            # Import here to avoid circular import at module level
            from bot.services import onboarding
            await onboarding.handle_timeout(bot, chat_id, user_id)
        finally:
            _tasks.pop(key, None)

    _tasks[key] = asyncio.create_task(_run())
    log.info("Scheduled removal for user %d in chat %d in %.1f min", user_id, chat_id, timeout_minutes)
    return f"removal:{chat_id}:{user_id}"


def cancel_removal(chat_id: int, user_id: int) -> bool:
    """Cancel a scheduled removal. Returns True if cancelled."""
    key = (chat_id, user_id)
    task = _tasks.pop(key, None)
    if task and not task.done():
        task.cancel()
        log.info("Cancelled removal for user %d in chat %d", user_id, chat_id)
        return True
    return False


def cancel_all() -> None:
    """Cancel all pending removal tasks (for shutdown)."""
    for task in _tasks.values():
        if not task.done():
            task.cancel()
    _tasks.clear()
