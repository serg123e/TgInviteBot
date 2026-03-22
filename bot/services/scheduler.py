from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.services import onboarding

log = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


def get_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler(timezone="UTC")
    return _scheduler


def schedule_removal(chat_id: int, user_id: int, timeout_minutes: float, bot) -> str:
    """Schedule a member removal after timeout. Returns the job ID."""
    scheduler = get_scheduler()
    job_id = f"removal:{chat_id}:{user_id}"

    # Remove existing job if any
    existing = scheduler.get_job(job_id)
    if existing:
        existing.remove()

    run_at = datetime.now(timezone.utc) + timedelta(minutes=timeout_minutes)
    scheduler.add_job(
        onboarding.handle_timeout,
        "date",
        run_date=run_at,
        args=[bot, chat_id, user_id],
        id=job_id,
        replace_existing=True,
    )
    log.info("Scheduled removal for user %d in chat %d at %s", user_id, chat_id, run_at)
    return job_id


def cancel_removal(chat_id: int, user_id: int) -> bool:
    """Cancel a scheduled removal. Returns True if cancelled."""
    scheduler = get_scheduler()
    job_id = f"removal:{chat_id}:{user_id}"
    job = scheduler.get_job(job_id)
    if job:
        job.remove()
        log.info("Cancelled removal for user %d in chat %d", user_id, chat_id)
        return True
    return False
