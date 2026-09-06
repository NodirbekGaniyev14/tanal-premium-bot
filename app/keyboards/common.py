from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app import texts
from app.db.models import SetModel

REMOVE = ReplyKeyboardRemove()


def contact_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=texts.ASK_CONTACT_BUTTON, request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=texts.MENU_GRAMMAR),
                KeyboardButton(text=texts.MENU_READING_LISTENING),
            ],
            [
                KeyboardButton(text=texts.MENU_WRITING),
                KeyboardButton(text=texts.MENU_SPEAKING),
            ],
            [KeyboardButton(text=texts.MENU_STATS)],
        ],
        resize_keyboard=True,
    )


def sets_kb(
    sets: list[SetModel],
    *,
    marks: dict[str, str] | None = None,
    back_to: str | None = None,
) -> InlineKeyboardMarkup:
    """To'plamlar ro'yxati. `marks` — set_code → progres belgisi (✅ / 🔓 / 🔒)."""
    marks = marks or {}
    builder = InlineKeyboardBuilder()
    for item in sets:
        mark = marks.get(item.set_code, "")
        label = f"{mark} {item.title}".strip()
        builder.button(text=label, callback_data=f"set:{item.set_code}")
    builder.adjust(1)
    if back_to:
        builder.row(
            InlineKeyboardButton(text=texts.BTN_BACK, callback_data=f"nav:{back_to}")
        )
    return builder.as_markup()


def set_card_kb(item: SetModel, *, can_solve: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if item.theory_file_id:
        builder.button(text=texts.BTN_THEORY, callback_data=f"theory:{item.set_code}")
    if item.audio_file_id:
        builder.button(text=texts.BTN_AUDIO, callback_data=f"audio:{item.set_code}")
    if item.pdf_file_id:
        label = texts.BTN_TEST if item.section == "grammar_topic" else texts.BTN_PDF
        builder.button(text=label, callback_data=f"pdf:{item.set_code}")
    if can_solve:
        builder.button(
            text="✏️ Javoblarni yuborish", callback_data=f"solve:{item.set_code}"
        )
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text=texts.BTN_BACK, callback_data=f"nav:{item.section}")
    )
    return builder.as_markup()


def collecting_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=texts.BTN_FINISH, callback_data="ans:finish")],
            [InlineKeyboardButton(text=texts.BTN_CANCEL, callback_data="ans:cancel")],
        ]
    )


def confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=texts.BTN_CONFIRM, callback_data="ans:grade"),
                InlineKeyboardButton(text=texts.BTN_REDO, callback_data="ans:redo"),
            ],
            [InlineKeyboardButton(text=texts.BTN_CANCEL, callback_data="ans:cancel")],
        ]
    )


def result_kb(
    *, set_code: str, attempt_id: int, can_retry: bool, theory: bool
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if theory:
        builder.button(text=texts.BTN_THEORY, callback_data=f"theory:{set_code}")
    if can_retry:
        builder.button(text=texts.BTN_RETRY, callback_data=f"solve:{set_code}")
    builder.button(text=texts.BTN_STATS, callback_data="nav:stats")
    builder.button(text=texts.BTN_REPORT, callback_data=f"report:{attempt_id}")
    builder.adjust(2)
    return builder.as_markup()


def audio_again_kb(message_id: int) -> InlineKeyboardMarkup:
    """Audio qayta yuborilmaydi — o'sha xabarga qaytariladi."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=texts.BTN_AUDIO_AGAIN, callback_data=f"goto:{message_id}"
                )
            ]
        ]
    )
