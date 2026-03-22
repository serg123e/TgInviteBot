"""Shared fixtures for tests."""

import aiosqlite
import pytest_asyncio

import bot.db.connection as _conn


@pytest_asyncio.fixture
async def db():
    """In-memory SQLite database with schema applied."""
    conn = await aiosqlite.connect(":memory:")
    conn.row_factory = aiosqlite.Row

    with open("migrations/001_initial.sql") as f:
        await conn.executescript(f.read())
    with open("migrations/002_admin_message_id.sql") as f:
        await conn.executescript(f.read())

    original = _conn._db
    _conn._db = conn
    yield conn
    _conn._db = original
    await conn.close()
