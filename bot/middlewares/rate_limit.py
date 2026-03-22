from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

log = logging.getLogger(__name__)


class RateLimitMiddleware(BaseMiddleware):
    """Simple rate limiter: ensures minimum interval between handler executions."""

    def __init__(self, min_interval: float = 0.05):
        self._min_interval = min_interval
        self._last_call = 0.0
        self._lock = asyncio.Lock()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with self._lock:
            now = time.monotonic()
            wait = self._min_interval - (now - self._last_call)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_call = time.monotonic()

        return await handler(event, data)
