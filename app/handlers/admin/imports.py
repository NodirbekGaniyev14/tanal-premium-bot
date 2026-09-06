"""Excel importi: fayl yuboriladi → tekshiriladi → baza yangilanadi."""

from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app import texts
from app.filters import IsAdmin
from app.services.importer import KINDS, detect_kind, run_import
from app.states import AdminImport

router = Router(name="admin-imports")
router.message.filter(IsAdmin())

#: Telegram orqali qabul qilinadigan maksimal Excel hajmi.
MAX_XLSX_BYTES = 10 * 1024 * 1024


@router.message(Command("help"))
async def admin_help(message: Message) -> None:
    await message.answer(texts.ADMIN_HELP)


@router.message(Command("import"))
async def start_import(message: Message, state: FSMContext) -> None:
    await state.set_state(AdminImport.waiting_file)
    await message.answer(texts.ADMIN_IMPORT_WAIT)


@router.message(AdminImport.waiting_file, F.document)
@router.message(F.document.file_name.endswith(".xlsx"))
async def handle_xlsx(
    message: Message, state: FSMContext, session: AsyncSession, bot: Bot
) -> None:
    document = message.document
    assert document is not None

    kind = detect_kind(document.file_name or "")
    if kind is None:
        await message.answer(
            "Fayl nomidan turini aniqlay olmadim. Nomida shulardan biri bo'lsin: "
            + " · ".join(KINDS)
        )
        return

    if (document.file_size or 0) > MAX_XLSX_BYTES:
        await message.answer("Fayl juda katta (10 MB dan oshmasin).")
        return

    buffer = await bot.download(document.file_id)
    data = buffer.read() if buffer else b""

    report = await run_import(session, kind, data)
    if not report.ok:
        await session.rollback()
    await message.answer(report.as_text())
    await state.clear()
