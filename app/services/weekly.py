"""Haftalik xulosa — o'quvchini qaytarib olib keladigan eng arzon vosita."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import repo
from app.db.models import AnswerKey, Attempt, SetModel, Student
from app.enums import Section
from app.services.tutor import weekly_summary_lines

_SECTION_LABEL = {
    Section.GRAMMAR_TOPIC.value: "mavzu testi",
    Section.GRAMMAR_MOCK.value: "grammatika mock",
    Section.READING.value: "reading",
    Section.LISTENING.value: "listening",
}


async def _tag_totals(session: AsyncSession, set_codes: set[str]) -> dict[str, int]:
    if not set_codes:
        return {}
    rows = (
        await session.execute(
            select(AnswerKey.tag).where(
                AnswerKey.set_code.in_(set_codes), AnswerKey.tag.is_not(None)
            )
        )
    ).scalars()
    totals: dict[str, int] = {}
    for tag in rows:
        totals[tag] = totals.get(tag, 0) + 1
    return totals


def _avg_percent(attempts: list[Attempt]) -> int | None:
    scored = [a for a in attempts if a.total]
    if not scored:
        return None
    return round(sum(a.score * 100 / a.total for a in scored) / len(scored))


async def build_weekly_summary(
    session: AsyncSession, student: Student, *, now: datetime | None = None
) -> str | None:
    """Faqat o'sha hafta faol bo'lgan o'quvchi uchun matn qaytaradi."""
    now = now or datetime.now(UTC)
    week_start = now - timedelta(days=7)
    prev_start = now - timedelta(days=14)

    this_week = await repo.attempts_since(session, student.id, week_start)
    if not this_week:
        return None

    prev_week = [
        a
        for a in await repo.attempts_since(session, student.id, prev_start)
        if a.created_at < week_start
    ]

    sections: dict[str, int] = {}
    set_codes = {a.set_code for a in this_week}
    sets_by_code = {
        row.set_code: row
        for row in (
            await session.execute(select(SetModel).where(SetModel.set_code.in_(set_codes)))
        ).scalars()
    }
    for attempt in this_week:
        item = sets_by_code.get(attempt.set_code)
        label = _SECTION_LABEL.get(item.section if item else "", "test")
        sections[label] = sections.get(label, 0) + 1

    totals = await _tag_totals(session, set_codes)
    wrong_by_tag: dict[str, int] = {}
    for attempt in this_week:
        for tag, count in (attempt.weak_tags or {}).items():
            wrong_by_tag[tag] = wrong_by_tag.get(tag, 0) + int(count)

    rates: list[tuple[str, int]] = []
    for tag, total in totals.items():
        if total < 2:
            continue
        wrong = wrong_by_tag.get(tag, 0)
        rates.append((tag, round((total - wrong) * 100 / total)))
    rates.sort(key=lambda kv: kv[1])

    worst = rates[0] if rates else None
    best = rates[-1] if len(rates) > 1 else None

    level_change: tuple[str, str] | None = None
    levels_now = [a.level for a in this_week if a.level]
    levels_prev = [a.level for a in prev_week if a.level]
    if levels_now and levels_prev and levels_now[-1] != levels_prev[-1]:
        level_change = (levels_prev[-1], levels_now[-1])

    next_steps: list[str] = []
    if worst and worst[1] < 70:
        next_steps.append(f"«{worst[0]}» mavzusini qayta ko'rib chiqing")
    untouched = [
        label
        for section, label in _SECTION_LABEL.items()
        if not any(
            sets_by_code.get(a.set_code) and sets_by_code[a.set_code].section == section
            for a in this_week
        )
    ]
    if untouched:
        next_steps.append(f"Bu hafta tegilmagan bo'lim: {untouched[0]} — bittasini boshlang")

    period = f"{week_start:%d.%m} – {now:%d.%m}"
    return weekly_summary_lines(
        period=period,
        attempts_count=sections,
        avg_percent=_avg_percent(this_week) or 0,
        prev_avg_percent=_avg_percent(prev_week),
        best_tag=best,
        worst_tag=worst,
        level_change=level_change,
        next_steps=next_steps,
    )
