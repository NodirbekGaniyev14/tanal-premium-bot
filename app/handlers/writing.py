"""Yozish bo'limi: topshiriq → insho rasmlari → Gemini → raqamlangan tuzatishlar."""

from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app import texts
from app.config import get_settings
from app.db import repo
from app.db.models import Student
from app.enums import AiKind
from app.filters import HasStudent
from app.keyboards.ai import (
    ai_tasks_kb,
    writing_collect_kb,
    writing_parts_kb,
    writing_result_kb,
)
from app.services.ai.client import MediaPart
from app.services.ai.render import render_writing
from app.services.ai.service import check_limit, review_writing
from app.states import Writing

logger = logging.getLogger(__name__)

router = Router(name="writing")
router.message.filter(HasStudent())
router.callback_query.filter(HasStudent())

_OWN_TASK_TYPE = "task_2"


async def show_menu(message: Message, session: AsyncSession, state: FSMContext) -> None:
    await state.clear()
    parts = await repo.list_ai_parts(session, str(AiKind.WRITING))
    await message.answer(texts.WRITING_MENU, reply_markup=writing_parts_kb(parts))


@router.callback_query(F.data == "nav:writing")
async def back_to_menu(
    call: CallbackQuery, session: AsyncSession, state: FSMContext
) -> None:
    if call.message is not None:
        await show_menu(call.message, session, state)
    await call.answer()


@router.callback_query(F.data.startswith("wpart:"))
async def pick_part(
    call: CallbackQuery, session: AsyncSession, state: FSMContext
) -> None:
    part = (call.data or "").split(":", 1)[1]
    if call.message is None:
        await call.answer()
        return

    if part == "own":
        await state.set_state(Writing.own_task)
        await call.message.answer(texts.WRITING_OWN_TASK_ASK)
        await call.answer()
        return

    tasks = await repo.list_ai_tasks(session, str(AiKind.WRITING), part)
    if not tasks:
        await call.answer(texts.AI_EMPTY_BANK, show_alert=True)
        return

    await state.set_state(Writing.choosing_task)
    await call.message.answer(
        texts.WRITING_PICK_TASK, reply_markup=ai_tasks_kb(tasks, "wtask")
    )
    await call.answer()


@router.message(Writing.own_task, F.text)
async def own_task(message: Message, state: FSMContext) -> None:
    await state.set_state(Writing.collecting_pages)
    await state.update_data(
        task_id=None,
        task_prompt=(message.text or "").strip()[:2000],
        task_type=_OWN_TASK_TYPE,
        pages=[],
    )
    await message.answer(texts.WRITING_SEND_PHOTOS, reply_markup=writing_collect_kb())


@router.callback_query(F.data.startswith("wtask:"))
async def pick_task(
    call: CallbackQuery, session: AsyncSession, state: FSMContext, bot: Bot
) -> None:
    task_id = int((call.data or "").split(":", 1)[1])
    task = await repo.get_ai_task(session, task_id)
    if task is None or call.message is None:
        await call.answer(texts.AI_EMPTY_BANK, show_alert=True)
        return

    await state.set_state(Writing.collecting_pages)
    await state.update_data(
        task_id=task.id,
        task_prompt=task.prompt_text,
        task_type=task.part or _OWN_TASK_TYPE,
        pages=[],
    )

    if task.image_file_id:
        await bot.send_photo(call.message.chat.id, task.image_file_id)

    await call.message.answer(
        texts.WRITING_TASK_CARD.format(
            title=task.title, prompt=task.prompt_text, hint=texts.WRITING_SEND_PHOTOS
        ),
        reply_markup=writing_collect_kb(),
    )
    await call.answer()


@router.message(Writing.collecting_pages, F.photo)
async def collect_page(message: Message, state: FSMContext) -> None:
    limit = get_settings().writing_max_pages
    data = await state.get_data()
    pages: list[str] = list(data.get("pages", []))

    if len(pages) >= limit:
        await message.answer(texts.WRITING_TOO_MANY_PAGES.format(limit=limit))
        return

    assert message.photo is not None
    pages.append(message.photo[-1].file_id)
    await state.update_data(pages=pages)
    await message.answer(
        texts.WRITING_PAGE_ADDED.format(count=len(pages)),
        reply_markup=writing_collect_kb(),
    )


@router.message(Writing.collecting_pages, F.document)
async def collect_page_as_document(message: Message, state: FSMContext) -> None:
    """Rasm hujjat sifatida yuborilsa ham qabul qilamiz."""
    document = message.document
    if document is None or not (document.mime_type or "").startswith("image/"):
        await message.answer(texts.WRITING_NEED_PHOTO)
        return

    limit = get_settings().writing_max_pages
    data = await state.get_data()
    pages: list[str] = list(data.get("pages", []))
    if len(pages) >= limit:
        await message.answer(texts.WRITING_TOO_MANY_PAGES.format(limit=limit))
        return

    pages.append(document.file_id)
    await state.update_data(pages=pages)
    await message.answer(
        texts.WRITING_PAGE_ADDED.format(count=len(pages)),
        reply_markup=writing_collect_kb(),
    )


@router.message(Writing.collecting_pages, F.text)
async def wrong_input(message: Message) -> None:
    await message.answer(texts.WRITING_NEED_PHOTO, reply_markup=writing_collect_kb())


@router.callback_query(F.data == "wr:cancel")
async def cancel(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    if call.message is not None:
        await call.message.answer(texts.CANCELLED)
    await call.answer()


@router.callback_query(Writing.collecting_pages, F.data == "wr:done")
async def submit(
    call: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    student: Student,
    bot: Bot,
) -> None:
    data = await state.get_data()
    pages: list[str] = list(data.get("pages", []))
    if not pages or call.message is None:
        await call.answer(texts.WRITING_NO_PAGES, show_alert=True)
        return

    limit = await check_limit(session, student)
    if not limit.allowed:
        await call.answer(
            texts.AI_LIMIT_REACHED.format(limit=limit.limit), show_alert=True
        )
        return

    await call.answer()
    await state.clear()
    progress = await call.message.answer(texts.WRITING_CHECKING)

    images: list[MediaPart] = []
    for file_id in pages:
        buffer = await bot.download(file_id)
        images.append(
            MediaPart(data=buffer.read() if buffer else b"", mime_type="image/jpeg")
        )

    task = (
        await repo.get_ai_task(session, int(data["task_id"]))
        if data.get("task_id")
        else None
    )
    outcome = await review_writing(
        session,
        student=student,
        task=task,
        task_prompt=str(data.get("task_prompt", "")),
        task_type=str(data.get("task_type", _OWN_TASK_TYPE)),
        images=images,
        file_ids=pages,
    )

    if not outcome.ok or outcome.review is None:
        await progress.edit_text(texts.AI_FAILED)
        return

    review = outcome.review
    if getattr(review, "unreadable", False):
        await progress.edit_text(texts.WRITING_UNREADABLE)
        return

    left = await check_limit(session, student)
    await progress.edit_text(
        render_writing(review, demo=outcome.demo)  # type: ignore[arg-type]
        + f"\n\n{texts.AI_LEFT_TODAY.format(left=left.left, limit=left.limit)}",
        reply_markup=writing_result_kb(
            outcome.submission.id,
            has_corrected=bool(getattr(review, "corrected_text", "")),
        ),
    )


@router.callback_query(F.data.startswith("wtext:"))
async def corrected_text(
    call: CallbackQuery, session: AsyncSession, student: Student
) -> None:
    submission_id = int((call.data or "").split(":", 1)[1])
    submission = await repo.get_ai_submission(session, submission_id)
    if submission is None or submission.student_id != student.id:
        await call.answer(texts.NOT_FOR_YOU, show_alert=True)
        return

    text = str((submission.feedback or {}).get("corrected_text", "")).strip()
    if not text or call.message is None:
        await call.answer("Tuzatilgan matn saqlanmagan.", show_alert=True)
        return

    await call.message.answer(f"<b>Tuzatilgan to'liq matn</b>\n\n{text[:3500]}")
    await call.answer()
