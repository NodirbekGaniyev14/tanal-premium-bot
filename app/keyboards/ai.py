from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app import texts
from app.db.models import AiTask

_WRITING_PART_LABEL = {"task1": "Task 1", "task2": "Task 2"}


def writing_parts_kb(parts: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for part in parts:
        builder.button(
            text=_WRITING_PART_LABEL.get(part, part), callback_data=f"wpart:{part}"
        )
    builder.button(text=texts.BTN_OWN_TASK, callback_data="wpart:own")
    builder.adjust(2)
    return builder.as_markup()


def speaking_parts_kb(parts: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for part in parts:
        builder.button(text=f"Part {part}", callback_data=f"spart:{part}")
    builder.adjust(3)
    return builder.as_markup()


def ai_tasks_kb(tasks: list[AiTask], prefix: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for task in tasks:
        builder.button(text=task.title, callback_data=f"{prefix}:{task.id}")
    builder.adjust(1)
    return builder.as_markup()


def writing_collect_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=texts.BTN_WRITING_DONE, callback_data="wr:done"
                )
            ],
            [InlineKeyboardButton(text=texts.BTN_CANCEL, callback_data="wr:cancel")],
        ]
    )


def writing_result_kb(submission_id: int, *, has_corrected: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if has_corrected:
        builder.button(
            text=texts.BTN_CORRECTED_TEXT, callback_data=f"wtext:{submission_id}"
        )
    builder.button(text="✍️ Yana yozish", callback_data="nav:writing")
    builder.adjust(1)
    return builder.as_markup()


def speaking_result_kb(
    submission_id: int, part: str, *, has_model_answer: bool
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if has_model_answer:
        builder.button(
            text=texts.BTN_MODEL_ANSWER, callback_data=f"smodel:{submission_id}"
        )
    builder.button(text=texts.BTN_NEXT_QUESTION, callback_data=f"spart:{part}")
    builder.adjust(1)
    return builder.as_markup()


def speaking_ready_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=texts.BTN_CANCEL, callback_data="wr:cancel")]
        ]
    )
