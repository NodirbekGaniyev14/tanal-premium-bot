"""AI natijalarini o'quvchiga ko'rsatish."""

from __future__ import annotations

from html import escape

from app.services.ai.schemas import SpeakingReview, WritingReview

#: Bitta jumla, kelajakdagi bahs-munozaraning yarmini yo'q qiladi.
DISCLAIMER = (
    "<i>Bu AI bahosi, real imtihon natijasi emas — yakuniy baho o'qituvchiniki.</i>"
)
DEMO_BANNER = (
    "🧪 <b>DEMO rejimi</b> — natija namunaviy, Gemini chaqirilmadi.\n"
    "Haqiqiy baho uchun <code>GEMINI_API_KEY</code> qo'yiladi."
)

#: Natija xabari juda uzun bo'lmasin — qolganini alohida tugma ko'rsatadi.
MAX_ERRORS_SHOWN = 8


def _band(value: float) -> str:
    return f"{value:.1f}"


def render_writing(review: WritingReview, *, demo: bool = False) -> str:
    scores = review.scores.normalized()
    lines: list[str] = []
    if demo:
        lines.extend([DEMO_BANNER, ""])

    lines.append(f"<b>Taxminiy band: {_band(scores.overall)}</b>")
    lines.append(
        f"TA {_band(scores.ta)} · CC {_band(scores.cc)} · "
        f"LR {_band(scores.lr)} · GRA {_band(scores.gra)}"
    )
    if review.word_count:
        lines.append(f"So'z soni: {review.word_count}")

    if review.errors:
        shown = review.errors[:MAX_ERRORS_SHOWN]
        total = review.error_count_total or len(review.errors)
        lines.append("")
        lines.append(f"<b>XATOLAR</b> ({total} ta topildi, asosiy {len(shown)} tasi)")
        for index, error in enumerate(shown, start=1):
            lines.append(
                f"{index}. \"{escape(error.original)}\" → "
                f"<b>\"{escape(error.correction)}\"</b>"
            )
            if error.why:
                lines.append(f"   <i>{escape(error.why)}</i>")

    if review.strength:
        lines.extend(["", f"<b>KUCHLI TOMONI</b>\n{escape(review.strength)}"])
    if review.fix_first:
        lines.append(f"\n<b>NIMANI TUZATISH</b>\n{escape(review.fix_first)}")

    lines.extend(["", DISCLAIMER])
    return "\n".join(lines)


def render_speaking(review: SpeakingReview, *, demo: bool = False) -> str:
    scores = review.scores.normalized()
    lines: list[str] = []
    if demo:
        lines.extend([DEMO_BANNER, ""])

    if review.transcript:
        lines.extend(["<b>Transkript</b>", f"<i>{escape(review.transcript)}</i>", ""])

    lines.append(f"<b>Taxminiy band: {_band(scores.overall)}</b>")
    lines.append(
        f"Fluency {_band(scores.fc)} · Lexical {_band(scores.lr)} · "
        f"Grammar {_band(scores.gra)} · Pronunciation {_band(scores.pron)}"
    )
    if review.wpm:
        lines.append(
            f"Nutq tezligi: {review.wpm} so'z/daq · "
            f"uzun pauza: {review.long_pauses} ta"
        )

    if review.grammar_errors:
        lines.extend(["", "<b>GRAMMATIK XATOLAR</b>"])
        for error in review.grammar_errors[:MAX_ERRORS_SHOWN]:
            lines.append(
                f"• \"{escape(error.quote)}\" → <b>\"{escape(error.correction)}\"</b>"
            )

    if review.advice:
        lines.extend(["", "<b>3 TA ANIQ TAVSIYA</b>"])
        lines.extend(
            f"{i}. {escape(item)}" for i, item in enumerate(review.advice[:3], start=1)
        )

    lines.extend(["", DISCLAIMER])
    return "\n".join(lines)
