"""To'plam kartasi: material yuborish va javob yig'ishni boshlash."""

from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app import texts
from app.db import repo
from app.db.models import SetModel, Student
from app.enums import FileKind
from app.filters import HasStudent
from app.keyboards.common import audio_again_kb, collecting_kb, set_card_kb
from app.services.files import send_material
from app.states import Solving

router = Router(name="sets")
router.callback_query.filter(HasStudent())


def _code(call: CallbackQuery) -> str:
    return (call.data or "").split(":", 1)[1]


async def _load(
    call: CallbackQuery, session: AsyncSession
) -> SetModel | None:
    item = await repo.get_set(session, _code(call))
    if item is None or not item.is_active:
        await call.answer(texts.FILE_MISSING, show_alert=True)
        return None
    return item


async def _attempts_state(
    session: AsyncSession, student: Student, item: SetModel
) -> tuple[int, int]:
    used = await repo.count_attempts(session, student.id, item.set_code)
    return used, item.attempts_allowed


@router.callback_query(F.data.startswith("set:"))
async def open_set(
    call: CallbackQuery, session: AsyncSession, student: Student
) -> None:
    item = await _load(call, session)
    if item is None or call.message is None:
        return

    if item.requires:
        solved = await repo.solved_set_codes(session, student.id)
        if item.requires not in solved:
            required = await repo.get_set(session, item.requires)
            await call.answer(
                texts.SET_LOCKED.format(
                    required=required.title if required else item.requires
                ),
                show_alert=True,
            )
            return

    used, allowed = await _attempts_state(session, student, item)
    extra = texts.SEND_ANSWERS_HINT if used < allowed else texts.SET_NO_ATTEMPTS.format(
        allowed=allowed, used=used
    )
    await call.message.edit_text(
        texts.SET_CARD.format(
            title=item.title,
            total_q=item.total_q,
            used=used,
            allowed=allowed,
            extra=extra,
        ),
        reply_markup=set_card_kb(item, can_solve=used < allowed),
    )
    await call.answer()


@router.callback_query(F.data.startswith(("pdf:", "theory:", "audio:")))
async def send_file(
    call: CallbackQuery, session: AsyncSession, student: Student, bot: Bot
) -> None:
    item = await _load(call, session)
    if item is None or call.message is None:
        return

    prefix = (call.data or "").split(":", 1)[0]
    kind = {"pdf": FileKind.PDF, "theory": FileKind.THEORY, "audio": FileKind.AUDIO}[prefix]

    await call.answer("Yuborilmoqda…")
    sent = await send_material(
        bot,
        session,
        chat_id=call.message.chat.id,
        student=student,
        item=item,
        kind=kind,
        caption=item.title,
    )
    if sent is None:
        await call.message.answer(texts.FILE_MISSING)
        return

    if kind is FileKind.AUDIO:
        await call.message.answer(
            "Tinglab bo'lgach javoblarni yuboring.",
            reply_markup=audio_again_kb(sent.message_id),
        )


@router.callback_query(F.data.startswith("goto:"))
async def goto_message(call: CallbackQuery) -> None:
    """Audio qayta yuborilmaydi — o'quvchi o'sha xabarga qaytariladi."""
    message_id = int((call.data or "").split(":", 1)[1])
    if call.message is None:
        await call.answer()
        return
    await call.message.answer("🎧 Audio yuqorida:", reply_to_message_id=message_id)
    await call.answer()


@router.callback_query(F.data.startswith("solve:"))
async def start_solving(
    call: CallbackQuery, session: AsyncSession, student: Student, state: FSMContext
) -> None:
    item = await _load(call, session)
    if item is None or call.message is None:
        return

    used, allowed = await _attempts_state(session, student, item)
    if used >= allowed:
        await call.answer(
            texts.SET_NO_ATTEMPTS.format(allowed=allowed, used=used), show_alert=True
        )
        return

    await state.set_state(Solving.collecting)
    await state.set_data(
        {
            "set_code": item.set_code,
            "total_q": item.total_q,
            "section": item.section,
            "raw_chunks": [],
            "answers": {},
        }
    )
    await call.message.answer(
        f"<b>{item.title}</b> — {item.total_q} ta savol.\n\n{texts.SEND_ANSWERS_HINT}",
        reply_markup=collecting_kb(),
    )
    await call.answer()
