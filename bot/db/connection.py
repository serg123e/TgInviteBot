import logging
import os

import aiosqlite

log = logging.getLogger(__name__)

_db: aiosqlite.Connection | None = None


async def init_db(path: str) -> aiosqlite.Connection:
    global _db
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    _db = await aiosqlite.connect(path)
    _db.row_factory = aiosqlite.Row
    await _db.execute("PRAGMA journal_mode=WAL")
    await _db.execute("PRAGMA foreign_keys=ON")
    log.info("Database opened: %s", path)
    return _db


async def close_db() -> None:
    global _db
    if _db:
        await _db.close()
        _db = None
        log.info("Database closed")


def get_db() -> aiosqlite.Connection:
    if _db is None:
        raise RuntimeError("Database is not initialized. Call init_db() first.")
    return _db
