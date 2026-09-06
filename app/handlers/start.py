"""/start va telefon raqami orqali kirish.

Uch holat: topildi · topilmadi · boshqa akkauntda — har biriga alohida javob
va adminga signal.
"""

from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app import texts
from app.config import get_settings
from app.db import repo
from app.db.models import Student
from app.enums import StudentStatus
from app.keyboards.common import contact_kb, main_menu_kb
from app.services.notify import notify_admins
from app.states import Registration
from app.utils.phone import normalize_phone

router = Router(name="start")


def _cohort_name(student: Student) -> str:
    return student.cohort.name if student.cohort else "—"


async def _greet(message: Message, student: Student) -> None:
    await message.answer(
        texts.ACCESS_OK.format(name=student.full_name, cohort=_cohort_name(student)),
        reply_markup=main_menu_kb(),
    )


@router.message(CommandStart())
async def cmd_start(
    message: Message, state: FSMContext, student: Student | None
) -> None:
    await state.clear()
    if student and student.status == StudentStatus.ACTIVE:
        await _greet(message, student)
        return
    await state.set_state(Registration.waiting_contact)
    await message.answer(texts.WELCOME, reply_markup=contact_kb())


@router.message(F.contact)
async def got_contact(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    bot: Bot,
) -> None:
    contact = message.contact
    user = message.from_user
    assert contact is not None and user is not None

    # O'zganing kontaktini uzatib kirishning oldini oladi.
    if contact.user_id != user.id:
        await message.answer(texts.CONTACT_NOT_OWN, reply_markup=contact_kb())
        return

    phone = normalize_phone(contact.phone_number)
    if not phone:
        await message.answer(texts.CONTACT_BAD_FORMAT, reply_markup=contact_kb())
        return

    settings = get_settings()
    student = await repo.get_student_by_phone(session, phone)

    if student is None:
        await message.answer(texts.ACCESS_NOT_FOUND)
        await notify_admins(
            bot,
            settings.admin_chat_id,
            texts.SIGNAL_UNKNOWN_PHONE.format(
                name=user.full_name,
                username=user.username or "—",
                tg_id=user.id,
                phone=phone,
            ),
        )
        return

    if student.tg_id and student.tg_id != user.id:
        await message.answer(texts.ACCESS_TAKEN)
        await notify_admins(
            bot,
            settings.admin_chat_id,
            texts.SIGNAL_PHONE_TAKEN.format(
                phone=phone,
                owner=student.full_name,
                name=user.full_name,
                username=user.username or "—",
                tg_id=user.id,
            ),
        )
        return

    if student.status == StudentStatus.BLOCKED:
        await message.answer(texts.ACCESS_BLOCKED)
        return

    if repo.access_expired(student):
        until = student.access_until or (
            student.cohort.ends_at if student.cohort else None
        )
        await message.answer(texts.ACCESS_EXPIRED.format(until=until))
        return

    await repo.activate_student(session, student, user.id, user.username)
    await state.clear()
    await _greet(message, student)
