from __future__ import annotations

import asyncio
import logging
import time
from collections import OrderedDict
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

log = logging.getLogger(__name__)

MAX_TRACKED_CHATS = 2000


class RateLimitMiddleware(BaseMiddleware):
    """Per-chat rate limiter: ensures minimum interval between handler executions per chat."""

    def __init__(self, min_interval: float = 0.05):
        self._min_interval = min_interval
        self._last_calls: OrderedDict[int, float] = OrderedDict()
        self._locks: dict[int, asyncio.Lock] = {}

    def _get_lock(self, chat_id: int) -> asyncio.Lock:
        if chat_id not in self._locks:
            self._locks[chat_id] = asyncio.Lock()
        return self._locks[chat_id]

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        chat_id = getattr(event, "chat", None)
        chat_id = chat_id.id if chat_id else 0

        async with self._get_lock(chat_id):
            now = time.monotonic()
            last = self._last_calls.get(chat_id, 0.0)
            wait = self._min_interval - (now - last)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_calls[chat_id] = time.monotonic()
            self._last_calls.move_to_end(chat_id)

            # Evict oldest entries when over limit
            while len(self._last_calls) > MAX_TRACKED_CHATS:
                evicted_id, _ = self._last_calls.popitem(last=False)
                self._locks.pop(evicted_id, None)

        return await handler(event, data)
