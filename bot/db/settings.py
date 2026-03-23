from __future__ import annotations

import logging
from dataclasses import dataclass

from bot.db.connection import get_db

log = logging.getLogger(__name__)

DEFAULT_WELCOME = (
    "Здравствуйте! Представьтесь, пожалуйста, в течение {timeout} минут: "
    "напишите кто вы, чем занимаетесь и зачем пришли в группу."
)


@dataclass
class ChatSettings:
    chat_id: int
    chat_title: str | None
    welcome_text: str
    timeout_minutes: int
    min_response_length: int
    ai_validation_enabled: bool
    ban_on_remove: bool
    ignore_bots: bool
    is_active: bool


async def get_or_create(chat_id: int, chat_title: str | None = None) -> ChatSettings:
    db = get_db()
    async with db.execute(
        "SELECT * FROM chat_settings WHERE chat_id = ?", (chat_id,)
    ) as cur:
        row = await cur.fetchone()

    if row:
        return _row_to_settings(row)

    await db.execute(
        """
        INSERT INTO chat_settings (chat_id, chat_title)
        VALUES (?, ?)
        ON CONFLICT (chat_id) DO UPDATE SET chat_title = excluded.chat_title
        """,
        (chat_id, chat_title),
    )
    await db.commit()

    async with db.execute(
        "SELECT * FROM chat_settings WHERE chat_id = ?", (chat_id,)
    ) as cur:
        row = await cur.fetchone()

    log.info("Created chat_settings for chat_id=%d", chat_id)
    return _row_to_settings(row)


async def update(chat_id: int, **kwargs) -> ChatSettings | None:
    db = get_db()
    if not kwargs:
        return await get_or_create(chat_id)

    allowed = {
        "chat_title", "welcome_text", "timeout_minutes", "min_response_length",
        "ai_validation_enabled", "ban_on_remove", "ignore_bots", "is_active",
    }

    set_parts = []
    values = []
    for key, value in kwargs.items():
        if key not in allowed:
            raise ValueError(f"Unknown setting: {key}")
        set_parts.append(f"{key} = ?")
        values.append(value)
    values.append(chat_id)

    query = f"""
        UPDATE chat_settings
        SET {', '.join(set_parts)}, updated_at = datetime('now')
        WHERE chat_id = ?
    """
    await db.execute(query, values)
    await db.commit()

    async with db.execute(
        "SELECT * FROM chat_settings WHERE chat_id = ?", (chat_id,)
    ) as cur:
        row = await cur.fetchone()

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
        ai_validation_enabled=bool(row["ai_validation_enabled"]),
        ban_on_remove=bool(row["ban_on_remove"]),
        ignore_bots=bool(row["ignore_bots"]),
        is_active=bool(row["is_active"]),
    )
