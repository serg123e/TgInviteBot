from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime

from bot.db.connection import get_db

log = logging.getLogger(__name__)


@dataclass
class GroupMember:
    id: int
    chat_id: int
    telegram_user_id: int
    username: str | None
    first_name: str | None
    last_name: str | None
    joined_at: str
    prompt_sent_at: str | None
    prompt_message_id: int | None
    response_text: str | None
    responded_at: str | None
    ai_validation_result: dict | None
    status: str
    removed_at: str | None
    removal_reason: str | None
    is_whitelisted: bool


async def upsert_member(
    chat_id: int,
    user_id: int,
    username: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
) -> GroupMember:
    db = get_db()
    await db.execute(
        """
        INSERT INTO group_members (chat_id, telegram_user_id, username, first_name, last_name, status)
        VALUES (?, ?, ?, ?, ?, 'joined')
        ON CONFLICT (chat_id, telegram_user_id) DO UPDATE SET
            username = excluded.username,
            first_name = excluded.first_name,
            last_name = excluded.last_name,
            joined_at = datetime('now'),
            status = 'joined',
            response_text = NULL,
            responded_at = NULL,
            ai_validation_result = NULL,
            removed_at = NULL,
            removal_reason = NULL,
            prompt_sent_at = NULL,
            prompt_message_id = NULL,
            updated_at = datetime('now')
        """,
        (chat_id, user_id, username, first_name, last_name),
    )
    await db.commit()

    async with db.execute(
        "SELECT * FROM group_members WHERE chat_id = ? AND telegram_user_id = ?",
        (chat_id, user_id),
    ) as cur:
        row = await cur.fetchone()

    return _row_to_member(row)


async def get_member(chat_id: int, user_id: int) -> GroupMember | None:
    db = get_db()
    async with db.execute(
        "SELECT * FROM group_members WHERE chat_id = ? AND telegram_user_id = ?",
        (chat_id, user_id),
    ) as cur:
        row = await cur.fetchone()
    return _row_to_member(row) if row else None


async def update_status(
    chat_id: int, user_id: int, status: str, **kwargs
) -> GroupMember | None:
    db = get_db()
    set_parts = ["status = ?", "updated_at = datetime('now')"]
    values: list = [status]

    for key, value in kwargs.items():
        set_parts.append(f"{key} = ?")
        if key == "ai_validation_result" and isinstance(value, dict):
            values.append(json.dumps(value))
        elif isinstance(value, datetime):
            values.append(value.isoformat())
        else:
            values.append(value)

    values.extend([chat_id, user_id])

    query = f"""
        UPDATE group_members
        SET {', '.join(set_parts)}
        WHERE chat_id = ? AND telegram_user_id = ?
    """
    await db.execute(query, values)
    await db.commit()

    async with db.execute(
        "SELECT * FROM group_members WHERE chat_id = ? AND telegram_user_id = ?",
        (chat_id, user_id),
    ) as cur:
        row = await cur.fetchone()

    return _row_to_member(row) if row else None


async def get_pending_members(chat_id: int | None = None) -> list[GroupMember]:
    db = get_db()
    if chat_id:
        async with db.execute(
            "SELECT * FROM group_members WHERE chat_id = ? AND status IN ('joined', 'prompt_sent') ORDER BY joined_at",
            (chat_id,),
        ) as cur:
            rows = await cur.fetchall()
    else:
        async with db.execute(
            "SELECT * FROM group_members WHERE status IN ('joined', 'prompt_sent') ORDER BY joined_at"
        ) as cur:
            rows = await cur.fetchall()
    return [_row_to_member(r) for r in rows]


async def get_members_by_status(chat_id: int, status: str) -> list[GroupMember]:
    db = get_db()
    async with db.execute(
        "SELECT * FROM group_members WHERE chat_id = ? AND status = ? ORDER BY joined_at",
        (chat_id, status),
    ) as cur:
        rows = await cur.fetchall()
    return [_row_to_member(r) for r in rows]


async def set_whitelisted(chat_id: int, user_id: int, whitelisted: bool = True) -> GroupMember | None:
    db = get_db()
    await db.execute(
        """
        UPDATE group_members SET is_whitelisted = ?, updated_at = datetime('now')
        WHERE chat_id = ? AND telegram_user_id = ?
        """,
        (int(whitelisted), chat_id, user_id),
    )
    await db.commit()

    async with db.execute(
        "SELECT * FROM group_members WHERE chat_id = ? AND telegram_user_id = ?",
        (chat_id, user_id),
    ) as cur:
        row = await cur.fetchone()

    return _row_to_member(row) if row else None


def _row_to_member(row) -> GroupMember:
    ai_result = row["ai_validation_result"]
    if isinstance(ai_result, str):
        ai_result = json.loads(ai_result)
    return GroupMember(
        id=row["id"],
        chat_id=row["chat_id"],
        telegram_user_id=row["telegram_user_id"],
        username=row["username"],
        first_name=row["first_name"],
        last_name=row["last_name"],
        joined_at=row["joined_at"],
        prompt_sent_at=row["prompt_sent_at"],
        prompt_message_id=row["prompt_message_id"],
        response_text=row["response_text"],
        responded_at=row["responded_at"],
        ai_validation_result=ai_result,
        status=row["status"],
        removed_at=row["removed_at"],
        removal_reason=row["removal_reason"],
        is_whitelisted=bool(row["is_whitelisted"]),
    )
