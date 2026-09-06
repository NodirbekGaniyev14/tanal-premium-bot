"""Yordamchi ustoz — 1-daraja: natijadan keyingi tavsiya.

Sehr yo'q: xato savollar `answer_keys.tag` bilan solishtiriladi va
takrorlanayotgan naqsh topiladi. Gemini talab qilinmaydi.
"""

from __future__ import annotations

from html import escape

from app.services.answer_engine.grader import GradeResult

#: Tavsiya berish uchun bitta tagda kamida shuncha xato bo'lishi kerak.
MIN_TAG_HITS = 2
#: Bitta tag "asosiy sabab" deb aytilishi uchun xatolarning shuncha ulushi.
DOMINANT_SHARE = 0.5


def _wrong_nos_for_tag(grade: GradeResult, tag: str) -> list[int]:
    return [r.q_no for r in grade.results if not r.correct and r.tag == tag]


def build_advice(grade: GradeResult) -> str | None:
    """Natija ostida chiqadigan bitta-ikkita jumlalik tavsiya."""
    if not grade.wrong_nos:
        return "💡 Xatosiz. Keyingi bosqichga o'tishingiz mumkin."

    if not grade.weak_tags:
        if grade.percent < 60:
            return (
                "💡 Natija past. Nazariyani qayta o'qib, testni yana bir bor yeching."
            )
        return None

    ranked = sorted(grade.weak_tags.items(), key=lambda kv: (-kv[1], kv[0]))
    top_tag, top_hits = ranked[0]
    wrong_total = len(grade.wrong_nos)

    runner_up = ranked[1][1] if len(ranked) > 1 else 0
    dominant = (
        top_hits >= MIN_TAG_HITS
        and top_hits / wrong_total >= DOMINANT_SHARE
        # teng bo'lsa bitta mavzuga ishora qilish noto'g'ri — ikkalasini aytamiz
        and (runner_up < MIN_TAG_HITS or top_hits > runner_up)
    )
    if dominant:
        nos = ", ".join(str(n) for n in _wrong_nos_for_tag(grade, top_tag))
        return (
            f"💡 {wrong_total} ta xatoning {top_hits} tasi ({nos}) — "
            f"<b>{escape(top_tag)}</b>.\n"
            "Shu mavzuni qayta ko'rib chiqing."
        )

    strong = [(tag, hits) for tag, hits in ranked if hits >= MIN_TAG_HITS][:2]
    if len(strong) >= 2:
        first, second = strong
        return (
            "💡 Xatolaringiz ikki joyda to'plangan: "
            f"<b>{escape(first[0])}</b> ({first[1]} ta) va "
            f"<b>{escape(second[0])}</b> ({second[1]} ta).\n"
            "Shu ikkisidan boshlang."
        )
    if strong:
        tag, hits = strong[0]
        return f"💡 Eng ko'p xato <b>{escape(tag)}</b> da ({hits} ta)."

    return None


def weekly_summary_lines(
    *,
    period: str,
    attempts_count: dict[str, int],
    avg_percent: int,
    prev_avg_percent: int | None,
    best_tag: tuple[str, int] | None,
    worst_tag: tuple[str, int] | None,
    level_change: tuple[str, str] | None,
    next_steps: list[str],
) -> str:
    """2-daraja: yakshanba kuni yuboriladigan haftalik xulosa."""
    lines = [f"📊 <b>Haftalik xulosa · {period}</b>", ""]

    done = " · ".join(f"{count} {name}" for name, count in attempts_count.items() if count)
    lines.append(f"Bu hafta: {done or 'faollik yo‘q'}")

    if prev_avg_percent is None:
        lines.append(f"O'rtacha: {avg_percent}%")
    else:
        delta = avg_percent - prev_avg_percent
        arrow = "📈" if delta > 0 else ("📉" if delta < 0 else "➡️")
        lines.append(
            f"O'rtacha: {avg_percent}%  (o'tgan hafta {prev_avg_percent}%)  "
            f"{arrow} {delta:+d}"
        )

    if best_tag:
        lines.append(f"Eng kuchli: {escape(best_tag[0])} — {best_tag[1]}%")
    if worst_tag:
        lines.append(f"Eng zaif: {escape(worst_tag[0])} — {worst_tag[1]}%")

    if level_change:
        old, new = level_change
        lines.append(f"\nDarajangiz: {old} → <b>{new}</b> 🎉")

    if next_steps:
        lines.append("\n<b>Keyingi qadam:</b>")
        lines.extend(f"{i}. {step}" for i, step in enumerate(next_steps, start=1))

    return "\n".join(lines)
