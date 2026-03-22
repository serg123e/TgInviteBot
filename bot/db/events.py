from __future__ import annotations

import json
import logging

from bot.db.connection import get_pool

log = logging.getLogger(__name__)


async def log_event(
    event_type: str,
    chat_id: int | None = None,
    user_id: int | None = None,
    details: dict | None = None,
) -> None:
    pool = get_pool()
    await pool.execute(
        """
        INSERT INTO event_logs (chat_id, telegram_user_id, event_type, details)
        VALUES ($1, $2, $3, $4::jsonb)
        """,
        chat_id,
        user_id,
        event_type,
        json.dumps(details) if details else None,
    )
