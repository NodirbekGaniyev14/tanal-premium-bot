"""Admin: to'plamlar holati, statistika, oqimlar, e'lon, ko'rib chiqish rejimi."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError, TelegramRetryAfter
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import texts
from app.config import get_settings
from app.db import repo
from app.db.models import AiSubmission, AnswerKey, Attempt, Student
from app.enums import StudentStatus
from app.filters import IsAdmin
from app.services.ai.service import daily_limit
from app.services.demo_seed import seed_demo
from app.states import Broadcast

logger = logging.getLogger(__name__)

router = Router(name="admin-stats")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

#: Telegram cheklovi ~30 xabar/sekund; ehtiyot bo'lib sekinroq yuboramiz.
_BROADCAST_DELAY = 0.05


@router.message(Command("sets"))
async def sets_status(message: Message, session: AsyncSession) -> None:
    items = await repo.list_all_sets(session)
    if not items:
        await message.answer("Hali birorta to'plam import qilinmagan.")
        return

    key_counts = dict(
        (
            await session.execute(
                select(AnswerKey.set_code, func.count()).group_by(AnswerKey.set_code)
            )
        ).all()
    )

    lines = ["<b>To'plamlar</b>", ""]
    for item in items:
        problems: list[str] = []
        if not item.pdf_file_id and item.pdf_file:
            problems.append("PDF yuklanmagan")
        if item.audio_file and not item.audio_file_id:
            problems.append("audio yuklanmagan")
        if item.theory_file and not item.theory_file_id:
            problems.append("nazariya yuklanmagan")
        keys = int(key_counts.get(item.set_code, 0))
        if keys != item.total_q:
            problems.append(f"kalit {keys}/{item.total_q}")
        mark = "✅" if not problems else "⚠️"
        suffix = f" — {', '.join(problems)}" if problems else ""
        lines.append(f"{mark} <code>{item.set_code}</code> {item.title}{suffix}")

    await message.answer("\n".join(lines))


@router.message(Command("stats"))
async def overall_stats(message: Message, session: AsyncSession) -> None:
    total_students = int(
        (await session.execute(select(func.count()).select_from(Student))).scalar_one()
    )
    active = int(
        (
            await session.execute(
                select(func.count())
                .select_from(Student)
                .where(Student.status == StudentStatus.ACTIVE)
            )
        ).scalar_one()
    )
    attempts = int(
        (await session.execute(select(func.count()).select_from(Attempt))).scalar_one()
    )
    avg_percent = (
        await session.execute(select(func.avg(Attempt.score * 100.0 / Attempt.total)))
    ).scalar_one()

    top_tags = (
        await session.execute(
            select(AnswerKey.tag, func.count())
            .join(Attempt, Attempt.set_code == AnswerKey.set_code)
            .where(
                AnswerKey.tag.is_not(None),
                Attempt.wrong_nos.contains(func.to_jsonb(AnswerKey.q_no)),
            )
            .group_by(AnswerKey.tag)
            .order_by(func.count().desc())
            .limit(8)
        )
    ).all()

    lines = [
        "<b>Umumiy statistika</b>",
        "",
        f"O'quvchilar: {total_students} (faol {active})",
        f"Urinishlar: {attempts}",
        f"O'rtacha natija: {round(float(avg_percent)) if avg_percent else 0}%",
    ]
    if top_tags:
        lines.extend(["", "<b>Eng ko'p xato qilinadigan mavzular</b>"])
        lines.extend(f"• {tag} — {count} ta xato" for tag, count in top_tags)
    await message.answer("\n".join(lines))


@router.message(Command("cohorts"))
async def cohorts(message: Message, session: AsyncSession) -> None:
    items = await repo.list_cohorts(session)
    if not items:
        await message.answer("Oqimlar yo'q — students.xlsx ni import qiling.")
        return

    lines = ["<b>Oqimlar</b>", ""]
    for cohort in items:
        count = int(
            (
                await session.execute(
                    select(func.count())
                    .select_from(Student)
                    .where(Student.cohort_id == cohort.id)
                )
            ).scalar_one()
        )
        ends = f" · tugaydi {cohort.ends_at}" if cohort.ends_at else ""
        lines.append(f"• <b>{cohort.name}</b> — {count} o'quvchi{ends}")
    await message.answer("\n".join(lines))


@router.message(Command("ai"))
async def ai_status(message: Message, session: AsyncSession) -> None:
    settings = get_settings()
    since = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

    rows = (
        await session.execute(
            select(
                AiSubmission.kind,
                func.count(),
                func.coalesce(func.sum(AiSubmission.tokens_in), 0),
                func.coalesce(func.sum(AiSubmission.tokens_out), 0),
            )
            .where(AiSubmission.created_at >= since)
            .group_by(AiSubmission.kind)
        )
    ).all()
    errors = int(
        (
            await session.execute(
                select(func.count())
                .select_from(AiSubmission)
                .where(AiSubmission.created_at >= since, AiSubmission.status == "error")
            )
        ).scalar_one()
    )

    mode = (
        "🧪 DEMO (Gemini chaqirilmaydi)"
        if settings.ai_demo_mode
        else f"✅ {settings.gemini_model}"
    )
    lines = [
        "<b>AI holati</b>",
        "",
        f"Rejim: {mode}",
        f"Kunlik limit (bir o'quvchiga): {await daily_limit(session)}",
        "",
        "<b>Bugun</b>",
    ]
    if not rows:
        lines.append("so'rov yo'q")
    for kind, count, tokens_in, tokens_out in rows:
        lines.append(
            f"• {kind}: {count} ta · tokenlar {int(tokens_in)} / {int(tokens_out)}"
        )
    if errors:
        lines.append(f"❌ Xatolar: {errors}")

    await message.answer("\n".join(lines))


@router.message(Command("demo"))
async def seed_demo_content(
    message: Message, command: CommandObject, session: AsyncSession
) -> None:
    """Demo to'plamlar, kalitlar, darajalar va AI topshiriqlari.

    Ixtiyoriy argument — sinov o'quvchisining telefon raqami.
    """
    phone = (command.args or "").strip() or None
    name = "Demo o'quvchi"
    if message.from_user and phone:
        name = message.from_user.full_name
    await message.answer(await seed_demo(session, phone=phone, full_name=name))


@router.message(Command("preview"))
async def preview(
    message: Message, command: CommandObject, session: AsyncSession
) -> None:
    """O'quvchi ko'radigan ekranni admin o'zi sinaydi."""
    code = (command.args or "").strip()
    if not code:
        await message.answer("Foydalanish: <code>/preview GR-T03</code>")
        return

    item = await repo.get_set(session, code)
    if item is None:
        await message.answer(f"<code>{code}</code> topilmadi.")
        return

    keys = await repo.get_keys(session, code)
    tags = {k.tag for k in keys if k.tag}
    await message.answer(
        texts.SET_CARD.format(
            title=item.title,
            total_q=item.total_q,
            used=0,
            allowed=item.attempts_allowed,
            extra=texts.SEND_ANSWERS_HINT,
        )
        + f"\n\n<i>reveal: {'yes' if item.reveal else 'no'} · "
        f"kalit: {len(keys)}/{item.total_q} · teglar: {len(tags)}</i>"
    )


# --- e'lon -----------------------------------------------------------------


@router.message(Command("broadcast"))
async def broadcast_start(message: Message, state: FSMContext) -> None:
    await state.set_state(Broadcast.waiting_text)
    await message.answer("E'lon matnini yuboring. Bekor qilish: /cancel")


@router.message(Command("cancel"))
async def cancel_any(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(texts.CANCELLED)


@router.message(Broadcast.waiting_text, F.text)
async def broadcast_preview(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    recipients = await repo.list_active_student_tg_ids(session)
    await state.update_data(text=message.html_text)
    await state.set_state(Broadcast.confirming)
    await message.answer(
        f"Quyidagi matn <b>{len(recipients)}</b> ta faol o'quvchiga yuboriladi:\n\n"
        f"{message.html_text}",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Yuborish", callback_data="bc:go"),
                    InlineKeyboardButton(text="❌ Bekor", callback_data="bc:no"),
                ]
            ]
        ),
    )


@router.callback_query(Broadcast.confirming, F.data == "bc:no")
async def broadcast_cancel(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await call.answer(texts.CANCELLED, show_alert=True)


@router.callback_query(Broadcast.confirming, F.data == "bc:go")
async def broadcast_send(
    call: CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot
) -> None:
    data = await state.get_data()
    text = str(data.get("text", "")).strip()
    await state.clear()
    if not text or call.message is None:
        await call.answer()
        return

    recipients = await repo.list_active_student_tg_ids(session)
    await call.answer("Yuborilmoqda…")

    sent = failed = 0
    for tg_id in recipients:
        try:
            await bot.send_message(tg_id, text)
            sent += 1
        except TelegramRetryAfter as exc:
            await asyncio.sleep(exc.retry_after)
            try:
                await bot.send_message(tg_id, text)
                sent += 1
            except TelegramAPIError:
                failed += 1
        except TelegramAPIError:
            failed += 1
        await asyncio.sleep(_BROADCAST_DELAY)

    await call.message.answer(f"E'lon yakunlandi: ✅ {sent} · ❌ {failed}")
