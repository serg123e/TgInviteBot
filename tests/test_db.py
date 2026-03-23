"""Tests for DB layer: connection, members, settings, events."""

import pytest

from bot.db import connection, members, settings

# --- connection ---


@pytest.mark.asyncio
async def test_get_db_raises_without_init():
    """get_db() raises RuntimeError if init_db was not called."""
    import bot.db.connection as c
    original = c._db
    c._db = None
    with pytest.raises(RuntimeError, match="not initialized"):
        c.get_db()
    c._db = original


@pytest.mark.asyncio
async def test_init_and_close_db(tmp_path):
    """init_db creates a working connection; close_db tears it down."""
    path = str(tmp_path / "test.db")
    conn = await connection.init_db(path)
    assert conn is not None
    assert connection.get_db() is conn
    await connection.close_db()
    assert connection._db is None


# --- members ---


@pytest.mark.asyncio
async def test_upsert_and_get_member(db):
    m = await members.upsert_member(100, 1, "alice", "Alice", "A")
    assert m.chat_id == 100
    assert m.telegram_user_id == 1
    assert m.username == "alice"
    assert m.status == "joined"
    assert m.is_whitelisted is False

    fetched = await members.get_member(100, 1)
    assert fetched is not None
    assert fetched.username == "alice"


@pytest.mark.asyncio
async def test_get_member_not_found(db):
    assert await members.get_member(999, 999) is None


@pytest.mark.asyncio
async def test_upsert_resets_status_but_keeps_history(db):
    await members.upsert_member(100, 1, "alice", "Alice", None)
    await members.update_status(100, 1, "approved", response_text="hello")

    # Rejoin resets status but preserves previous response
    m2 = await members.upsert_member(100, 1, "alice_new", "Alice", None)
    assert m2.status == "joined"
    assert m2.response_text == "hello"
    assert m2.username == "alice_new"


@pytest.mark.asyncio
async def test_update_status(db):
    await members.upsert_member(100, 1, "bob", "Bob", None)
    updated = await members.update_status(100, 1, "prompt_sent", prompt_message_id=42)
    assert updated is not None
    assert updated.status == "prompt_sent"
    assert updated.prompt_message_id == 42


@pytest.mark.asyncio
async def test_update_status_rejects_unknown_column(db):
    await members.upsert_member(100, 1, "bob", "Bob", None)
    with pytest.raises(ValueError, match="Unknown column"):
        await members.update_status(100, 1, "joined", bad_column="x")


@pytest.mark.asyncio
async def test_update_status_with_ai_result(db):
    await members.upsert_member(100, 1, "bob", "Bob", None)
    ai = {"valid": True, "reason": "ok"}
    updated = await members.update_status(100, 1, "approved", ai_validation_result=ai)
    assert updated is not None
    assert updated.ai_validation_result == ai


@pytest.mark.asyncio
async def test_get_pending_members(db):
    await members.upsert_member(100, 1, "a", "A", None)
    await members.upsert_member(100, 2, "b", "B", None)
    await members.update_status(100, 2, "prompt_sent")
    await members.upsert_member(100, 3, "c", "C", None)
    await members.update_status(100, 3, "approved")

    # All pending
    pending = await members.get_pending_members()
    ids = {m.telegram_user_id for m in pending}
    assert 1 in ids  # joined
    assert 2 in ids  # prompt_sent
    assert 3 not in ids  # approved

    # Filtered by chat
    pending_100 = await members.get_pending_members(chat_id=100)
    assert len(pending_100) == 2
    pending_999 = await members.get_pending_members(chat_id=999)
    assert len(pending_999) == 0


@pytest.mark.asyncio
async def test_get_members_by_status(db):
    await members.upsert_member(100, 1, "a", "A", None)
    await members.upsert_member(100, 2, "b", "B", None)
    await members.update_status(100, 2, "approved")

    joined = await members.get_members_by_status(100, "joined")
    assert len(joined) == 1
    assert joined[0].telegram_user_id == 1

    approved = await members.get_members_by_status(100, "approved")
    assert len(approved) == 1


@pytest.mark.asyncio
async def test_set_whitelisted(db):
    await members.upsert_member(100, 1, "a", "A", None)

    m = await members.set_whitelisted(100, 1, True)
    assert m is not None
    assert m.is_whitelisted is True

    m2 = await members.set_whitelisted(100, 1, False)
    assert m2 is not None
    assert m2.is_whitelisted is False


@pytest.mark.asyncio
async def test_set_whitelisted_not_found(db):
    result = await members.set_whitelisted(999, 999)
    assert result is None


# --- settings ---


@pytest.mark.asyncio
async def test_get_or_create_new(db):
    cfg = await settings.get_or_create(100, "Test Chat")
    assert cfg.chat_id == 100
    assert cfg.timeout_minutes == 15
    assert cfg.is_active is True
    assert cfg.ai_validation_enabled is True


@pytest.mark.asyncio
async def test_get_or_create_existing(db):
    await settings.get_or_create(100, "Test Chat")
    cfg2 = await settings.get_or_create(100)
    assert cfg2.chat_id == 100


@pytest.mark.asyncio
async def test_update_settings(db):
    await settings.get_or_create(100, "Test Chat")
    updated = await settings.update(100, timeout_minutes=60, ban_on_remove=True)
    assert updated is not None
    assert updated.timeout_minutes == 60
    assert updated.ban_on_remove is True


@pytest.mark.asyncio
async def test_update_empty_kwargs(db):
    await settings.get_or_create(100)
    result = await settings.update(100)
    assert result is not None  # returns get_or_create result


@pytest.mark.asyncio
async def test_update_nonexistent_chat(db):
    result = await settings.update(999, timeout_minutes=10)
    assert result is None


