from __future__ import annotations

import logging
from dataclasses import dataclass

from bot.db.connection import get_pool

log = logging.getLogger(__name__)

DEFAULT_WELCOME = "Здравствуйте! Представьтесь, пожалуйста, в течение {timeout} минут: напишите кто вы, чем занимаетесь и зачем пришли в группу."


@dataclass
class ChatSettings:
    chat_id: int
    chat_title: str | None
    welcome_text: str
    timeout_minutes: int
    min_response_length: int
    ai_validation_enabled: bool
    ban_on_remove: bool
    ban_duration_hours: int | None
    whitelist_enabled: bool
    ignore_bots: bool
    is_active: bool


async def get_or_create(chat_id: int, chat_title: str | None = None) -> ChatSettings:
    pool = get_pool()
    row = await pool.fetchrow(
        "SELECT * FROM chat_settings WHERE chat_id = $1", chat_id
    )
    if row:
        return _row_to_settings(row)

    row = await pool.fetchrow(
        """
        INSERT INTO chat_settings (chat_id, chat_title)
        VALUES ($1, $2)
        ON CONFLICT (chat_id) DO UPDATE SET chat_title = EXCLUDED.chat_title
        RETURNING *
        """,
        chat_id,
        chat_title,
    )
    log.info("Created chat_settings for chat_id=%d", chat_id)
    return _row_to_settings(row)


async def update(chat_id: int, **kwargs) -> ChatSettings | None:
    pool = get_pool()
    if not kwargs:
        return await get_or_create(chat_id)

    set_parts = []
    values = []
    for i, (key, value) in enumerate(kwargs.items(), start=1):
        set_parts.append(f"{key} = ${i}")
        values.append(value)
    values.append(chat_id)

    query = f"""
        UPDATE chat_settings
        SET {', '.join(set_parts)}, updated_at = NOW()
        WHERE chat_id = ${len(values)}
        RETURNING *
    """
    row = await pool.fetchrow(query, *values)
    if row is None:
        return None
    return _row_to_settings(row)


def _row_to_settings(row) -> ChatSettings:
    return ChatSettings(
        chat_id=row["chat_id"],
        chat_title=row["chat_title"],
        welcome_text=row["welcome_text"],
        timeout_minutes=row["timeout_minutes"],
        min_response_length=row["min_response_length"],
        ai_validation_enabled=row["ai_validation_enabled"],
        ban_on_remove=row["ban_on_remove"],
        ban_duration_hours=row["ban_duration_hours"],
        whitelist_enabled=row["whitelist_enabled"],
        ignore_bots=row["ignore_bots"],
        is_active=row["is_active"],
    )
