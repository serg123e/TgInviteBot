#!/usr/bin/env python3
"""Telegram Onboarding Bot — entry point."""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import config
from bot.db.connection import close_db, init_db
from bot.handlers import admin, member_left, message, new_member
from bot.middlewares.rate_limit import RateLimitMiddleware
from bot.services.scheduler import get_scheduler
from bot.services import onboarding

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)


async def on_startup(bot: Bot) -> None:
    db = await init_db(config.sqlite_path)

    # Run migrations on startup
    from migrations.run_migrations import run
    run()
    log.info("Database ready: %s", config.sqlite_path)

    scheduler = get_scheduler()
    scheduler.start()
    log.info("Scheduler started")

    # Restore pending timers
    count = await onboarding.restore_timers(bot)
    log.info("Restored %d pending timers", count)

    me = await bot.get_me()
    log.info("Bot started: @%s (id=%d)", me.username, me.id)


async def on_shutdown(bot: Bot) -> None:
    scheduler = get_scheduler()
    scheduler.shutdown(wait=False)
    log.info("Scheduler stopped")

    await close_db()
    log.info("Database disconnected")


async def main() -> None:
    if not config.bot_token:
        log.error("BOT_TOKEN is required")
        sys.exit(1)
    if not config.admin_chat_id:
        log.error("ADMIN_CHAT_ID is required")
        sys.exit(1)

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()

    # Middleware
    dp.message.middleware(RateLimitMiddleware())

    # Register routers
    dp.include_router(new_member.router)
    dp.include_router(member_left.router)
    dp.include_router(admin.router)
    dp.include_router(message.router)  # Must be last (catches all text messages)

    # Lifecycle
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    log.info("Starting bot...")
    await dp.start_polling(bot, allowed_updates=["message", "chat_member", "callback_query"])


if __name__ == "__main__":
    asyncio.run(main())
