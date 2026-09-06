"""Materiallarni yetkazish: ism yozilgan PDF nusxasi + `file_id` keshi.

Fayllar bizda saqlanmaydi — Telegram CDN da turadi, bazada faqat `file_id`.
"""

from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.types import BufferedInputFile, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import repo
from app.db.models import SetModel, Student
from app.enums import FileKind
from app.services.pdf_stamp import stamp_pdf

logger = logging.getLogger(__name__)


def _source_file_id(item: SetModel, kind: FileKind) -> str | None:
    if kind is FileKind.PDF:
        return item.pdf_file_id
    if kind is FileKind.THEORY:
        return item.theory_file_id
    return item.audio_file_id


async def send_material(
    bot: Bot,
    session: AsyncSession,
    *,
    chat_id: int,
    student: Student,
    item: SetModel,
    kind: FileKind,
    caption: str | None = None,
) -> Message | None:
    """Kerakli faylni yuboradi. PDF bo'lsa — o'quvchi ismi yozilgan nusxasini."""
    source_id = _source_file_id(item, kind)
    if not source_id:
        return None

    if kind is FileKind.AUDIO:
        return await bot.send_audio(chat_id, source_id, caption=caption)

    cached = await repo.get_cached_file(session, student.id, item.set_code, kind)
    if cached:
        return await bot.send_document(chat_id, cached, caption=caption)

    try:
        buffer = await bot.download(source_id)
        raw = buffer.read() if buffer else b""
        stamped = stamp_pdf(
            raw, student_name=student.full_name, student_id=student.id
        )
        document = BufferedInputFile(stamped, filename=f"{item.set_code}.pdf")
    except Exception:
        logger.exception("PDF nusxalash muvaffaqiyatsiz: %s", item.set_code)
        # nusxalash ishlamasa ham o'quvchi materialsiz qolmasin
        return await bot.send_document(chat_id, source_id, caption=caption)

    message = await bot.send_document(chat_id, document, caption=caption)
    if message.document:
        await repo.cache_file(
            session, student.id, item.set_code, kind, message.document.file_id
        )
    return message
