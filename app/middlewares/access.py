"""Kirish nazorati: ro'yxatda bo'lmagan odam hech qanday handlerga o'tmaydi."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from app import texts
from app.db import repo
from app.enums import StudentStatus

#: Ro'yxatdan o'tishdan oldin ham ishlaydigan yagona buyruq.
_OPEN_COMMANDS = {"/start", "/help"}


class AccessMiddleware(BaseMiddleware):
    def __init__(self, admin_ids: set[int]) -> None:
        self.admin_ids = admin_ids

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user is None:
            return await handler(event, data)

        data["is_admin"] = user.id in self.admin_ids
        session = data["session"]
        student = await repo.get_student_by_tg(session, user.id)
        data["student"] = student

        if data["is_admin"]:
            if student:
                await repo.touch_last_seen(session, student.id)
            return await handler(event, data)

        if student is None:
            if self._is_registration_step(event):
                return await handler(event, data)
            await self._reply(event, texts.NEED_REGISTRATION)
            return None

        if student.status == StudentStatus.BLOCKED:
            await self._reply(event, texts.ACCESS_BLOCKED)
            return None

        if repo.access_expired(student):
            until = student.access_until or (
                student.cohort.ends_at if student.cohort else None
            )
            await self._reply(event, texts.ACCESS_EXPIRED.format(until=until))
            return None

        await repo.touch_last_seen(session, student.id)
        return await handler(event, data)

    @staticmethod
    def _is_registration_step(event: TelegramObject) -> bool:
        if not isinstance(event, Message):
            return False
        if event.contact is not None:
            return True
        text = (event.text or "").strip().split()
        return bool(text) and text[0] in _OPEN_COMMANDS

    @staticmethod
    async def _reply(event: TelegramObject, text: str) -> None:
        if isinstance(event, Message):
            await event.answer(text)
        elif isinstance(event, CallbackQuery):
            await event.answer(text, show_alert=True)
