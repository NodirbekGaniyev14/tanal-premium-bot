"""Asosiy menyu va bo'limlar bo'ylab harakat."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app import texts
from app.db import repo
from app.db.models import Student
from app.enums import Section
from app.filters import HasStudent
from app.keyboards.common import sets_kb

router = Router(name="menu")
router.message.filter(HasStudent())
router.callback_query.filter(HasStudent())

_SECTION_TITLES = {
    Section.GRAMMAR_TOPIC: "📐 Grammatika — mavzular",
    Section.GRAMMAR_MOCK: "📐 Grammatika — mocklar",
    Section.READING: "📖 Reading mocklari",
    Section.LISTENING: "🎧 Listening mocklari",
}


def _grammar_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=texts.GRAMMAR_TOPICS, callback_data="nav:grammar_topic"
                )
            ],
            [
                InlineKeyboardButton(
                    text=texts.GRAMMAR_MOCKS, callback_data="nav:grammar_mock"
                )
            ],
        ]
    )


def _rl_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📖 Reading", callback_data="nav:reading")],
            [InlineKeyboardButton(text="🎧 Listening", callback_data="nav:listening")],
        ]
    )


async def _section_view(
    session: AsyncSession, student: Student, section: Section
) -> tuple[str, InlineKeyboardMarkup | None]:
    items = await repo.list_sets(session, section.value)
    if not items:
        return texts.SECTION_EMPTY, None

    best = await repo.best_scores(session, student.id)
    solved = set(best)
    marks: dict[str, str] = {}
    for item in items:
        if item.set_code in best:
            score, total = best[item.set_code]
            marks[item.set_code] = f"✅ {score}/{total} ·"
        elif item.requires and item.requires not in solved:
            marks[item.set_code] = "🔒"
        else:
            marks[item.set_code] = "🔓"

    back = "grammar" if section.value.startswith("grammar") else "rl"
    return _SECTION_TITLES[section], sets_kb(items, marks=marks, back_to=back)


# --- reply tugmalari -------------------------------------------------------


@router.message(F.text == texts.MENU_GRAMMAR)
async def open_grammar(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(texts.GRAMMAR_MENU, reply_markup=_grammar_kb())


@router.message(F.text == texts.MENU_READING_LISTENING)
async def open_rl(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(texts.RL_MENU, reply_markup=_rl_kb())


@router.message(F.text == texts.MENU_WRITING)
async def open_writing(
    message: Message, session: AsyncSession, state: FSMContext
) -> None:
    from app.handlers import writing

    await writing.show_menu(message, session, state)


@router.message(F.text == texts.MENU_SPEAKING)
async def open_speaking(
    message: Message, session: AsyncSession, state: FSMContext
) -> None:
    from app.handlers import speaking

    await speaking.show_menu(message, session, state)


@router.message(F.text == texts.MENU_STATS)
async def open_stats(
    message: Message, session: AsyncSession, student: Student
) -> None:
    await message.answer(await _stats_text(session, student))


# --- inline navigatsiya ----------------------------------------------------


@router.callback_query(F.data.startswith("nav:"))
async def navigate(
    call: CallbackQuery, session: AsyncSession, student: Student, state: FSMContext
) -> None:
    target = (call.data or "").split(":", 1)[1]
    message = call.message
    if message is None:
        await call.answer()
        return

    await state.clear()

    if target == "grammar":
        await message.edit_text(texts.GRAMMAR_MENU, reply_markup=_grammar_kb())
    elif target == "rl":
        await message.edit_text(texts.RL_MENU, reply_markup=_rl_kb())
    elif target == "stats":
        await message.answer(await _stats_text(session, student))
    elif target in {s.value for s in Section}:
        text, markup = await _section_view(session, student, Section(target))
        await message.edit_text(text, reply_markup=markup)
    await call.answer()


async def _stats_text(session: AsyncSession, student: Student) -> str:
    attempts = await repo.student_attempts(session, student.id, limit=30)
    if not attempts:
        return texts.STATS_EMPTY

    lines = [texts.STATS_HEADER, ""]
    for attempt in attempts[:15]:
        item = await repo.get_set(session, attempt.set_code)
        title = item.title if item else attempt.set_code
        level = f" · {attempt.level}" if attempt.level else ""
        lines.append(
            f"{attempt.created_at:%d.%m} — {title}: "
            f"<b>{attempt.score}/{attempt.total}</b>{level}"
        )
    if len(attempts) > 15:
        lines.append(f"\n… va yana {len(attempts) - 15} ta urinish")
    return "\n".join(lines)
