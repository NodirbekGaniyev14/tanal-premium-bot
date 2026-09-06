"""Speaking bo'limi: savol → ovozli javob → Gemini → transkript va band.

Telegram ovozli xabari `.ogg` (Opus) — Gemini uni to'g'ridan-to'g'ri qabul
qiladi, konvertatsiya ham, alohida transkripsiya xizmati ham kerak emas.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import random

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app import texts
from app.config import get_settings
from app.db import repo
from app.db.models import Student
from app.enums import AiKind
from app.filters import HasStudent
from app.keyboards.ai import speaking_parts_kb, speaking_ready_kb, speaking_result_kb
from app.services.ai.client import MediaPart
from app.services.ai.render import render_speaking
from app.services.ai.service import check_limit, review_speaking
from app.states import Speaking

logger = logging.getLogger(__name__)

router = Router(name="speaking")
router.message.filter(HasStudent())
router.callback_query.filter(HasStudent())

#: Part 2 uchun tayyorgarlik vaqti.
PREP_SECONDS = 60


async def show_menu(message: Message, session: AsyncSession, state: FSMContext) -> None:
    await state.clear()
    parts = await repo.list_ai_parts(session, str(AiKind.SPEAKING))
    if not parts:
        await message.answer(texts.AI_EMPTY_BANK)
        return
    await message.answer(texts.SPEAKING_MENU, reply_markup=speaking_parts_kb(parts))


@router.callback_query(F.data == "nav:speaking")
async def back_to_menu(
    call: CallbackQuery, session: AsyncSession, state: FSMContext
) -> None:
    if call.message is not None:
        await show_menu(call.message, session, state)
    await call.answer()


async def _prep_timer(bot: Bot, chat_id: int, state: FSMContext, task_id: int) -> None:
    """1 daqiqadan keyin eslatadi — agar o'quvchi hali javob bermagan bo'lsa."""
    await asyncio.sleep(PREP_SECONDS)
    data = await state.get_data()
    if await state.get_state() != Speaking.waiting_voice.state:
        return
    if data.get("task_id") != task_id:
        return
    with contextlib.suppress(TelegramAPIError):
        await bot.send_message(chat_id, texts.SPEAKING_PREP_OVER)


@router.callback_query(F.data.startswith("spart:"))
async def pick_part(
    call: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
    bot: Bot,
) -> None:
    part = (call.data or "").split(":", 1)[1]
    if call.message is None:
        await call.answer()
        return

    tasks = await repo.list_ai_tasks(session, str(AiKind.SPEAKING), part)
    if not tasks:
        await call.answer(texts.AI_EMPTY_BANK, show_alert=True)
        return

    task = random.choice(tasks)  # noqa: S311 — savol tanlash, kriptografiya emas
    await state.set_state(Speaking.waiting_voice)
    await state.update_data(task_id=task.id, question=task.prompt_text, part=part)

    if part == "2":
        await call.message.answer(
            texts.SPEAKING_CUE_CARD.format(
                question=task.prompt_text, cue=task.cue_points or ""
            ),
            reply_markup=speaking_ready_kb(),
        )
        await call.message.answer(texts.SPEAKING_PREP)
        asyncio.create_task(  # noqa: RUF006 — fon eslatmasi, natijasi kutilmaydi
            _prep_timer(bot, call.message.chat.id, state, task.id)
        )
    else:
        await call.message.answer(
            texts.SPEAKING_QUESTION.format(part=part, question=task.prompt_text),
            reply_markup=speaking_ready_kb(),
        )
        await call.message.answer(texts.SPEAKING_SEND_VOICE)

    await call.answer()


@router.message(Speaking.waiting_voice, F.text)
async def need_voice(message: Message) -> None:
    await message.answer(texts.SPEAKING_NEED_VOICE)


@router.message(Speaking.waiting_voice, F.voice | F.audio)
async def got_voice(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    student: Student,
    bot: Bot,
) -> None:
    settings = get_settings()
    media = message.voice or message.audio
    if media is None:
        await message.answer(texts.SPEAKING_NEED_VOICE)
        return

    duration = int(media.duration or 0)
    if duration and duration < settings.speaking_min_sec:
        await message.answer(
            texts.SPEAKING_TOO_SHORT.format(
                sec=duration, min_sec=settings.speaking_min_sec
            )
        )
        return
    if duration > settings.speaking_max_sec:
        await message.answer(
            texts.SPEAKING_TOO_LONG.format(
                sec=duration, max_sec=settings.speaking_max_sec
            )
        )
        return

    limit = await check_limit(session, student)
    if not limit.allowed:
        await message.answer(texts.AI_LIMIT_REACHED.format(limit=limit.limit))
        return

    data = await state.get_data()
    await state.clear()
    progress = await message.answer(texts.SPEAKING_CHECKING)

    buffer = await bot.download(media.file_id)
    audio = MediaPart(
        data=buffer.read() if buffer else b"",
        mime_type=media.mime_type or "audio/ogg",
    )

    task = (
        await repo.get_ai_task(session, int(data["task_id"]))
        if data.get("task_id")
        else None
    )
    part = str(data.get("part", "1"))
    outcome = await review_speaking(
        session,
        student=student,
        task=task,
        question=str(data.get("question", "")),
        part=part,
        audio=audio,
        file_ids=[media.file_id],
    )

    if not outcome.ok or outcome.review is None:
        await progress.edit_text(texts.AI_FAILED)
        return

    review = outcome.review
    if getattr(review, "insufficient", False):
        await progress.edit_text(texts.SPEAKING_INSUFFICIENT)
        return

    left = await check_limit(session, student)
    await progress.edit_text(
        render_speaking(review, demo=outcome.demo)  # type: ignore[arg-type]
        + f"\n\n{texts.AI_LEFT_TODAY.format(left=left.left, limit=left.limit)}",
        reply_markup=speaking_result_kb(
            outcome.submission.id,
            part,
            has_model_answer=bool(getattr(review, "model_answer", "")),
        ),
    )


@router.callback_query(F.data.startswith("smodel:"))
async def model_answer(
    call: CallbackQuery, session: AsyncSession, student: Student
) -> None:
    submission_id = int((call.data or "").split(":", 1)[1])
    submission = await repo.get_ai_submission(session, submission_id)
    if submission is None or submission.student_id != student.id:
        await call.answer(texts.NOT_FOR_YOU, show_alert=True)
        return

    text = str((submission.feedback or {}).get("model_answer", "")).strip()
    if not text or call.message is None:
        await call.answer("Namuna javob saqlanmagan.", show_alert=True)
        return

    await call.message.answer(f"<b>7.5 darajali namuna javob</b>\n\n{text[:3500]}")
    await call.answer()
