"""Hech qaysi handler qabul qilmagan yangilanishlar.

Ikki holat: o'quvchi menyudan tashqari matn yozdi, yoki admin o'quvchi
menyusini bosdi (unga bog'langan `students` yozuvi yo'q).
"""

from __future__ import annotations

from aiogram import Router
from aiogram.types import CallbackQuery, Message

from app.db.models import Student
from app.keyboards.common import main_menu_kb

router = Router(name="fallback")

_ADMIN_HINT = (
    "Bu bo'lim o'quvchilar uchun — sizda o'quvchi yozuvi yo'q.\n"
    "Admin buyruqlari: /help"
)
_STUDENT_HINT = "Pastdagi menyudan bo'limni tanlang."


def _hint(student: Student | None, is_admin: bool) -> str:
    if student is not None:
        return _STUDENT_HINT
    return _ADMIN_HINT if is_admin else "Ro'yxatdan o'tish uchun: /start"


@router.message()
async def unknown_message(
    message: Message, student: Student | None = None, is_admin: bool = False
) -> None:
    markup = main_menu_kb() if student is not None else None
    await message.answer(_hint(student, is_admin), reply_markup=markup)


@router.callback_query()
async def unknown_callback(
    call: CallbackQuery, student: Student | None = None, is_admin: bool = False
) -> None:
    await call.answer(_hint(student, is_admin), show_alert=True)
