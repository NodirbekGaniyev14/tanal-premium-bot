"""Rejalashtirilgan ishlar: haftalik xulosa va faol bo'lmaganlarga eslatma."""

from __future__ import annotations

import asyncio
import logging
from contextlib import suppress
from datetime import UTC, datetime, timedelta

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db.models import Student
from app.enums import StudentStatus
from app.services.weekly import build_weekly_summary

logger = logging.getLogger(__name__)

_SEND_DELAY = 0.05
#: Shuncha kundan beri kirmaganlarga qisqa eslatma boradi.
_IDLE_DAYS = 7


async def send_weekly_summaries(bot: Bot, sessionmaker: async_sessionmaker) -> None:
    async with sessionmaker() as session:
        students = list(
            (
                await session.execute(
                    select(Student).where(
                        Student.status == StudentStatus.ACTIVE,
                        Student.tg_id.is_not(None),
                    )
                )
            ).scalars()
        )

        sent = 0
        for student in students:
            try:
                text = await build_weekly_summary(session, student)
            except Exception:
                logger.exception("Haftalik xulosa yig'ilmadi: %s", student.id)
                continue
            if not text or student.tg_id is None:
                continue
            try:
                await bot.send_message(student.tg_id, text)
                sent += 1
            except TelegramAPIError:
                logger.warning("Xulosa yuborilmadi: %s", student.tg_id)
            await asyncio.sleep(_SEND_DELAY)
        logger.info("Haftalik xulosa yuborildi: %s ta", sent)


async def nudge_inactive(bot: Bot, sessionmaker: async_sessionmaker) -> None:
    threshold = datetime.now(UTC) - timedelta(days=_IDLE_DAYS)
    async with sessionmaker() as session:
        students = list(
            (
                await session.execute(
                    select(Student).where(
                        Student.status == StudentStatus.ACTIVE,
                        Student.tg_id.is_not(None),
                        Student.last_seen_at.is_not(None),
                        Student.last_seen_at < threshold,
                    )
                )
            ).scalars()
        )
        for student in students:
            if student.tg_id is None:
                continue
            with suppress(TelegramAPIError):
                await bot.send_message(
                    student.tg_id,
                    "👋 Bir haftadan beri ko'rinmadingiz.\n"
                    "Bugun bitta mavzu testini yechsangiz, ritm buzilmaydi.",
                )
            await asyncio.sleep(_SEND_DELAY)


def setup_scheduler(
    bot: Bot, sessionmaker: async_sessionmaker, timezone_name: str
) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=timezone_name)
    scheduler.add_job(
        send_weekly_summaries,
        CronTrigger(day_of_week="sun", hour=19, minute=0),
        args=(bot, sessionmaker),
        id="weekly-summary",
        replace_existing=True,
    )
    scheduler.add_job(
        nudge_inactive,
        CronTrigger(day_of_week="wed", hour=18, minute=0),
        args=(bot, sessionmaker),
        id="nudge-inactive",
        replace_existing=True,
    )
    return scheduler
