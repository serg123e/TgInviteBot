from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime

from bot.db.connection import get_pool

log = logging.getLogger(__name__)


@dataclass
class GroupMember:
    id: int
    chat_id: int
    telegram_user_id: int
    username: str | None
    first_name: str | None
    last_name: str | None
    joined_at: datetime
    prompt_sent_at: datetime | None
    prompt_message_id: int | None
    response_text: str | None
    responded_at: datetime | None
    ai_validation_result: dict | None
    status: str
    removed_at: datetime | None
    removal_reason: str | None
    is_whitelisted: bool


async def upsert_member(
    chat_id: int,
    user_id: int,
    username: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
) -> GroupMember:
    pool = get_pool()
    row = await pool.fetchrow(
        """
        INSERT INTO group_members (chat_id, telegram_user_id, username, first_name, last_name, status)
        VALUES ($1, $2, $3, $4, $5, 'joined')
        ON CONFLICT (chat_id, telegram_user_id) DO UPDATE SET
            username = EXCLUDED.username,
            first_name = EXCLUDED.first_name,
            last_name = EXCLUDED.last_name,
            joined_at = NOW(),
            status = 'joined',
            response_text = NULL,
            responded_at = NULL,
            ai_validation_result = NULL,
            removed_at = NULL,
            removal_reason = NULL,
            prompt_sent_at = NULL,
            prompt_message_id = NULL,
            updated_at = NOW()
        RETURNING *
        """,
        chat_id, user_id, username, first_name, last_name,
    )
    return _row_to_member(row)


async def get_member(chat_id: int, user_id: int) -> GroupMember | None:
    pool = get_pool()
    row = await pool.fetchrow(
        "SELECT * FROM group_members WHERE chat_id = $1 AND telegram_user_id = $2",
        chat_id, user_id,
    )
    return _row_to_member(row) if row else None


async def update_status(
    chat_id: int, user_id: int, status: str, **kwargs
) -> GroupMember | None:
    pool = get_pool()
    set_parts = ["status = $3", "updated_at = NOW()"]
    values = [chat_id, user_id, status]

    for key, value in kwargs.items():
        idx = len(values) + 1
        if key == "ai_validation_result" and isinstance(value, dict):
            set_parts.append(f"{key} = ${idx}::jsonb")
            values.append(json.dumps(value))
        else:
            set_parts.append(f"{key} = ${idx}")
            values.append(value)

    query = f"""
        UPDATE group_members
        SET {', '.join(set_parts)}
        WHERE chat_id = $1 AND telegram_user_id = $2
        RETURNING *
    """
    row = await pool.fetchrow(query, *values)
    return _row_to_member(row) if row else None


async def get_pending_members(chat_id: int | None = None) -> list[GroupMember]:
    pool = get_pool()
    if chat_id:
        rows = await pool.fetch(
            "SELECT * FROM group_members WHERE chat_id = $1 AND status IN ('joined', 'prompt_sent') ORDER BY joined_at",
            chat_id,
        )
    else:
        rows = await pool.fetch(
            "SELECT * FROM group_members WHERE status IN ('joined', 'prompt_sent') ORDER BY joined_at"
        )
    return [_row_to_member(r) for r in rows]


async def get_members_by_status(chat_id: int, status: str) -> list[GroupMember]:
    pool = get_pool()
    rows = await pool.fetch(
        "SELECT * FROM group_members WHERE chat_id = $1 AND status = $2 ORDER BY joined_at",
        chat_id, status,
    )
    return [_row_to_member(r) for r in rows]


async def set_whitelisted(chat_id: int, user_id: int, whitelisted: bool = True) -> GroupMember | None:
    pool = get_pool()
    row = await pool.fetchrow(
        """
        UPDATE group_members SET is_whitelisted = $3, updated_at = NOW()
        WHERE chat_id = $1 AND telegram_user_id = $2
        RETURNING *
        """,
        chat_id, user_id, whitelisted,
    )
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
        is_whitelisted=row["is_whitelisted"],
    )
