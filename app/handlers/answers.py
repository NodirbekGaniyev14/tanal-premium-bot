"""Javob dvigatelining Telegram qismi: yig'ish → tasdiqlash → baholash → natija."""

from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app import texts
from app.config import get_settings
from app.db import repo
from app.db.models import Student
from app.enums import SCOPE_BY_SECTION, Section
from app.filters import HasStudent
from app.keyboards.common import collecting_kb, confirm_kb, result_kb
from app.services.answer_engine import grade, parse_answers, pick_level
from app.services.notify import notify_admins
from app.services.render import confirm_text, result_text
from app.services.tutor import build_advice
from app.states import Solving

router = Router(name="answers")
router.message.filter(HasStudent())
router.callback_query.filter(HasStudent())


def _joined(chunks: list[str]) -> str:
    return "\n".join(chunks)


@router.message(Solving.collecting, F.text)
async def collect(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    total_q = int(data["total_q"])
    chunks = list(data.get("raw_chunks", []))
    chunks.append(message.text or "")

    parsed = parse_answers(_joined(chunks), total_q)
    if parsed.is_empty:
        await message.answer(texts.ANSWERS_EMPTY, reply_markup=collecting_kb())
        return

    await state.update_data(raw_chunks=chunks)
    await message.answer(
        texts.ANSWERS_COLLECTED.format(filled=parsed.filled, total=total_q),
        reply_markup=collecting_kb(),
    )


@router.callback_query(Solving.collecting, F.data == "ans:finish")
async def finish(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    total_q = int(data["total_q"])
    parsed = parse_answers(_joined(data.get("raw_chunks", [])), total_q)

    if parsed.is_empty:
        await call.answer(texts.CONFIRM_NOTHING, show_alert=True)
        return

    await state.set_state(Solving.confirming)
    if call.message is not None:
        await call.message.answer(
            confirm_text(parsed, total_q), reply_markup=confirm_kb()
        )
    await call.answer()


@router.callback_query(Solving.confirming, F.data == "ans:redo")
async def redo(call: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(raw_chunks=[])
    await state.set_state(Solving.collecting)
    if call.message is not None:
        await call.message.answer(texts.SEND_ANSWERS_HINT, reply_markup=collecting_kb())
    await call.answer()


@router.callback_query(F.data == "ans:cancel")
async def cancel(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    if call.message is not None:
        await call.message.answer(texts.CANCELLED)
    await call.answer()


@router.callback_query(Solving.confirming, F.data == "ans:grade")
async def do_grade(
    call: CallbackQuery, state: FSMContext, session: AsyncSession, student: Student
) -> None:
    data = await state.get_data()
    set_code = str(data["set_code"])
    total_q = int(data["total_q"])
    raw = _joined(data.get("raw_chunks", []))

    item = await repo.get_set(session, set_code)
    if item is None:
        await state.clear()
        await call.answer(texts.FILE_MISSING, show_alert=True)
        return

    keys = await repo.get_keys(session, set_code)
    if not keys:
        await state.clear()
        await call.answer(texts.FILE_MISSING, show_alert=True)
        return

    parsed = parse_answers(raw, total_q)
    result = grade(parsed.answers, keys)

    scope = SCOPE_BY_SECTION.get(Section(item.section), item.section)
    bands = await repo.get_level_bands(session, scope)
    band = pick_level(bands, result.score) if bands else None

    used = await repo.count_attempts(session, student.id, set_code)
    if item.reveal:
        previous = await repo.last_attempt(session, student.id, set_code)
    else:
        previous = await repo.previous_attempt_in_section(
            session, student.id, item.section, exclude_set=set_code
        )

    attempt = await repo.create_attempt(
        session,
        student_id=student.id,
        set_code=set_code,
        attempt_no=used + 1,
        submitted_raw=raw,
        parsed={str(k): v for k, v in parsed.answers.items()},
        score=result.score,
        total=result.total,
        level=band.level if band else None,
        level_label=band.label if band else None,
        wrong_nos=result.wrong_nos,
        weak_tags=result.weak_tags,
    )

    await state.clear()

    text = result_text(
        title=item.title,
        grade=result,
        reveal=item.reveal,
        band=band,
        prev_score=previous.score if previous else None,
        prev_level=previous.level if previous else None,
        advice=build_advice(result),
    )
    if call.message is not None:
        await call.message.answer(
            text,
            reply_markup=result_kb(
                set_code=set_code,
                attempt_id=attempt.id,
                can_retry=used + 1 < item.attempts_allowed,
                theory=bool(item.theory_file_id),
            ),
        )
    await call.answer()


@router.callback_query(F.data.startswith("report:"))
async def report_bad_grading(
    call: CallbackQuery, session: AsyncSession, student: Student, bot: Bot
) -> None:
    """«⚠️ Noto'g'ri baholandi» — kalitni tuzatish uchun adminga signal."""
    attempt_id = int((call.data or "").split(":", 1)[1])
    attempt = await repo.get_attempt(session, attempt_id)
    if attempt is None or attempt.student_id != student.id:
        await call.answer(texts.NOT_FOR_YOU, show_alert=True)
        return

    await notify_admins(
        bot,
        get_settings().admin_chat_id,
        texts.SIGNAL_BAD_GRADING.format(
            name=student.full_name,
            tg_id=student.tg_id,
            set_code=attempt.set_code,
            attempt_no=attempt.attempt_no,
            score=attempt.score,
            total=attempt.total,
            wrong=", ".join(str(n) for n in attempt.wrong_nos) or "—",
            raw=attempt.submitted_raw[:600],
        ),
    )
    await call.answer(texts.REPORT_SENT, show_alert=True)
