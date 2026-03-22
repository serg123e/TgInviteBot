import logging

import asyncpg

log = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None


async def init_pool(dsn: str, *, min_size: int = 2, max_size: int = 10) -> asyncpg.Pool:
    global _pool
    _pool = await asyncpg.create_pool(dsn, min_size=min_size, max_size=max_size)
    log.info("Database pool created (min=%d, max=%d)", min_size, max_size)
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        log.info("Database pool closed")


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database pool is not initialized. Call init_pool() first.")
    return _pool
