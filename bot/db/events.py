from __future__ import annotations

import json
import logging

from bot.db.connection import get_db

log = logging.getLogger(__name__)


async def log_event(
    event_type: str,
    chat_id: int | None = None,
    user_id: int | None = None,
    details: dict | None = None,
) -> None:
    db = get_db()
    await db.execute(
        """
        INSERT INTO event_logs (chat_id, telegram_user_id, event_type, details)
        VALUES (?, ?, ?, ?)
        """,
        (chat_id, user_id, event_type, json.dumps(details) if details else None),
    )
    await db.commit()
