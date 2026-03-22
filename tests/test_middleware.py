"""Tests for rate limit middleware."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from bot.middlewares.rate_limit import RateLimitMiddleware


def _event(chat_id: int = 1):
    event = MagicMock()
    event.chat = MagicMock()
    event.chat.id = chat_id
    return event


@pytest.mark.asyncio
async def test_middleware_calls_handler():
    mw = RateLimitMiddleware(min_interval=0)
    handler = AsyncMock(return_value="result")
    event = _event()
    data = {}

    result = await mw(handler, event, data)

    assert result == "result"
    handler.assert_called_once_with(event, data)


@pytest.mark.asyncio
async def test_middleware_rate_limits():
    """Two rapid calls should still both succeed, with the second delayed."""
    mw = RateLimitMiddleware(min_interval=0.01)
    handler = AsyncMock(return_value="ok")

    r1 = await mw(handler, _event(), {})
    r2 = await mw(handler, _event(), {})

    assert r1 == "ok"
    assert r2 == "ok"
    assert handler.call_count == 2


@pytest.mark.asyncio
async def test_middleware_per_chat_independent():
    """Messages from different chats should not block each other."""
    mw = RateLimitMiddleware(min_interval=0.1)
    handler = AsyncMock(return_value="ok")

    # Two calls to different chats should not cause the second to wait
    import time
    start = time.monotonic()
    await mw(handler, _event(chat_id=1), {})
    await mw(handler, _event(chat_id=2), {})
    elapsed = time.monotonic() - start

    assert handler.call_count == 2
    # Should be fast since different chats
    assert elapsed < 0.1


@pytest.mark.asyncio
async def test_middleware_no_chat_attr():
    """Events without chat attribute should still work."""
    mw = RateLimitMiddleware(min_interval=0)
    handler = AsyncMock(return_value="ok")
    event = MagicMock(spec=[])  # no chat attr

    result = await mw(handler, event, {})
    assert result == "ok"
