from __future__ import annotations

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from app.db.models import Student


class HasStudent(BaseFilter):
    """O'quvchi handlerlari. Admin ro'yxatda bo'lmasa bu yerga tushmaydi —
    uni `fallback` routeri qabul qiladi."""

    async def __call__(
        self, event: Message | CallbackQuery, student: Student | None = None
    ) -> bool:
        return student is not None
