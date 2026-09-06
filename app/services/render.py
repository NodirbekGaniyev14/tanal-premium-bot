"""Tasdiqlash ekrani va natija matnini yig'ish."""

from __future__ import annotations

from html import escape

from app import texts
from app.services.answer_engine.grader import GradeResult
from app.services.answer_engine.levels import LevelBand
from app.services.answer_engine.parser import ParseResult

#: Bitta qatorda nechta javob ko'rsatiladi (qisqa, variantli javoblar uchun).
_GRID_COLUMNS = 5
#: Shu uzunlikkacha bo'lgan javoblar jadval ko'rinishida chiqadi.
_GRID_MAX_LEN = 3


def _nos(values: list[int]) -> str:
    return ", ".join(str(v) for v in values)


def confirm_text(parsed: ParseResult, total_q: int) -> str:
    """«Javoblaringizni shunday o'qidim» ekrani — baholashdan oldingi oxirgi to'siq."""
    if parsed.is_empty:
        return texts.CONFIRM_NOTHING

    compact = all(len(v) <= _GRID_MAX_LEN for v in parsed.answers.values())
    lines: list[str] = [texts.CONFIRM_HEADER, ""]

    if compact:
        row: list[str] = []
        for q_no in range(1, total_q + 1):
            value = parsed.answers.get(q_no, "?")
            row.append(f"{q_no}-{escape(value.upper())}")
            if len(row) == _GRID_COLUMNS:
                lines.append("  ".join(row))
                row = []
        if row:
            lines.append("  ".join(row))
        lines[2:] = [f"<code>{line}</code>" for line in lines[2:]]
    else:
        for q_no in range(1, total_q + 1):
            value = parsed.answers.get(q_no)
            shown = escape(value) if value else "—"
            lines.append(f"<code>{q_no:>3})</code> {shown}")

    lines.append("")
    if parsed.missing:
        lines.append(texts.CONFIRM_MISSING.format(nos=_nos(parsed.missing)))
    if parsed.out_of_range:
        lines.append(texts.CONFIRM_OUT_OF_RANGE.format(nos=_nos(parsed.out_of_range)))
    lines.append(texts.CONFIRM_ASK)
    return "\n".join(lines)


def _compare_block(
    grade: GradeResult, prev_score: int | None, prev_level: str | None
) -> str | None:
    if prev_score is None:
        return None
    suffix = f" · {prev_level}" if prev_level else ""
    delta = grade.score - prev_score
    if delta > 0:
        return texts.RESULT_COMPARE_UP.format(
            prev=prev_score, total=grade.total, prev_level=suffix, delta=delta
        )
    if delta < 0:
        return texts.RESULT_COMPARE_DOWN.format(
            prev=prev_score, total=grade.total, prev_level=suffix, delta=delta
        )
    return texts.RESULT_COMPARE_SAME.format(prev=prev_score, total=grade.total)


def result_text(
    *,
    title: str,
    grade: GradeResult,
    reveal: bool,
    band: LevelBand | None = None,
    prev_score: int | None = None,
    prev_level: str | None = None,
    advice: str | None = None,
) -> str:
    """`reveal=True` — mavzu testi (to'g'ri javoblar ko'rsatiladi).

    `reveal=False` — mock: faqat ball, daraja va xato raqamlari.
    """
    level_text = band.level if band else "—"
    if band and band.label:
        level_text = f"{band.level} ({band.label})"

    if reveal:
        header = texts.RESULT_TOPIC_HEADER.format(
            title=escape(title),
            score=grade.score,
            total=grade.total,
            percent=grade.percent,
        )
    else:
        header = texts.RESULT_MOCK_HEADER.format(
            title=escape(title), score=grade.score, total=grade.total, level=level_text
        )

    lines: list[str] = [header, ""]

    compare = _compare_block(grade, prev_score, prev_level)
    if compare:
        lines.extend([compare, ""])

    if not grade.wrong_nos:
        lines.append(texts.RESULT_NO_WRONG)
    else:
        lines.append(texts.RESULT_WRONG_LIST.format(nos=_nos(grade.wrong_nos)))
        if reveal:
            lines.append("")
            for item in grade.results:
                if item.correct:
                    continue
                given = escape(item.given.upper()) if item.given else "—"
                lines.append(
                    f"<code>{item.q_no:>3}</code> — siz: {given}  ·  "
                    f"to'g'ri: <b>{escape(item.expected)}</b>"
                )

    if advice:
        lines.extend(["", advice])

    return "\n".join(lines)
