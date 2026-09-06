"""Botni ishga tushirish. Polling — domen ham, webhook ham shart emas."""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from app.config import get_settings
from app.db.base import get_engine, get_sessionmaker
from app.handlers import build_router
from app.middlewares.access import AccessMiddleware
from app.middlewares.db import DbSessionMiddleware
from app.middlewares.throttle import ThrottleMiddleware
from app.scheduler import setup_scheduler

logger = logging.getLogger(__name__)


def _setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)-7s %(name)s — %(message)s",
    )


async def main() -> None:
    settings = get_settings()
    _setup_logging(settings.log_level)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    redis = Redis.from_url(settings.redis_url)
    dispatcher = Dispatcher(storage=RedisStorage(redis))

    sessionmaker = get_sessionmaker()
    admin_ids = set(settings.admin_ids)

    # Tartib muhim: avval sessiya, keyin kirish nazorati.
    for observer in (dispatcher.message, dispatcher.callback_query):
        observer.outer_middleware(DbSessionMiddleware(sessionmaker))
        observer.outer_middleware(AccessMiddleware(admin_ids))
        observer.middleware(ThrottleMiddleware())

    dispatcher.include_router(build_router())

    scheduler = setup_scheduler(bot, sessionmaker, settings.tz)
    scheduler.start()

    logger.info("Bot ishga tushdi (polling)")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dispatcher.start_polling(bot, allowed_updates=["message", "callback_query"])
    finally:
        scheduler.shutdown(wait=False)
        await redis.aclose()
        await bot.session.close()
        await get_engine().dispose()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("To'xtatildi")
