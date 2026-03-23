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
from bot.i18n import load as load_i18n
from bot.services import onboarding
from bot.services.scheduler import cancel_all

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)


async def on_startup(bot: Bot) -> None:
    # Run migrations before opening async connection
    from migrations.run_migrations import run
    run()

    await init_db(config.sqlite_path)
    log.info("Database ready: %s", config.sqlite_path)

    # Restore pending timers
    count = await onboarding.restore_timers(bot)
    log.info("Restored %d pending timers", count)

    me = await bot.get_me()
    log.info("Bot started: @%s (id=%d)", me.username, me.id)


async def on_shutdown(bot: Bot) -> None:
    cancel_all()
    log.info("Pending timers cancelled")

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

    # Register routers
    dp.include_router(new_member.router)
    dp.include_router(member_left.router)
    dp.include_router(admin.router)
    dp.include_router(message.router)  # Must be last (catches all text messages)

    # Lifecycle
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    load_i18n(config.lang)
    log.info("Starting bot...")
    await dp.start_polling(bot, allowed_updates=["message", "chat_member", "callback_query"])


if __name__ == "__main__":
    asyncio.run(main())
