"""Javob matnini o'qish.

O'quvchi javobni qanday yozishini oldindan bilib bo'lmaydi, shuning uchun
parser rejadagi barcha ko'rinishlarni qabul qiladi:

    1a 2b 3c 4d 5a          1. A  2. B  3. C        1-A, 2-B, 3-C
    a b c d a b             har qatorda bitta harf   1) moon / 2) TRUE / 3) 15 minutes

Parser hech qachon o'zi baholamaydi — natijasi avval o'quvchiga tasdiqlash
ekranida ko'rsatiladi.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

#: Bitta javobning maksimal uzunligi (uzun matn — javob emas, izoh).
MAX_ANSWER_LEN = 120

#: Unicode tire va bo'shliqlarni oddiysiga keltirish.
_TRANSLATE = str.maketrans(
    {
        "‐": "-",
        "‑": "-",
        "‒": "-",
        "–": "-",
        "—": "-",
        "―": "-",
        " ": " ",
        "​": "",
        "．": ".",
        "）": ")",
    }
)

#: Savol raqami belgisi: raqamdan keyin ajratgich (`. ) - :`) yoki
#: bo'shliqsiz harf (`1a`). "15 minutes" dagi 15 belgi sifatida o'qilmaydi,
#: chunki undan keyin bo'shliq bor, ajratgich yo'q.
_MARKER_RE = re.compile(
    r"(?:(?<=^)|(?<=[\s,;|]))(\d{1,3})(?:\s*[.)\-:]\s*|(?=[A-Za-z]))",
    re.MULTILINE,
)

#: Faqat harflardan iborat javob ("a b c d" yoki har qatorda bitta harf).
_LETTERS_ONLY_RE = re.compile(r"^[A-Ha-h][\s,;.|-]*$")

_TRAILING_JUNK_RE = re.compile(r"[\s,;.|]+$")


@dataclass(slots=True)
class ParseResult:
    """Parser natijasi. `answers` — savol raqami → o'quvchi javobi (asl ko'rinishda)."""

    answers: dict[int, str] = field(default_factory=dict)
    missing: list[int] = field(default_factory=list)
    out_of_range: list[int] = field(default_factory=list)
    duplicates: dict[int, list[str]] = field(default_factory=dict)
    mode: str = "empty"  # numbered | sequential | empty

    @property
    def filled(self) -> int:
        return len(self.answers)

    @property
    def is_empty(self) -> bool:
        return not self.answers


def _clean(text: str) -> str:
    return text.translate(_TRANSLATE).strip()


def _trim_answer(raw: str) -> str:
    value = _TRAILING_JUNK_RE.sub("", raw.strip())
    return value[:MAX_ANSWER_LEN].strip()


def _parse_numbered(text: str, total_q: int) -> ParseResult | None:
    """`1a 2b`, `1. A`, `1-A`, `1) moon` ko'rinishlari."""
    markers = list(_MARKER_RE.finditer(text))
    if not markers:
        return None

    result = ParseResult(mode="numbered")
    for idx, marker in enumerate(markers):
        q_no = int(marker.group(1))
        end = markers[idx + 1].start() if idx + 1 < len(markers) else len(text)
        answer = _trim_answer(text[marker.end() : end])

        if q_no < 1 or q_no > total_q:
            if q_no not in result.out_of_range:
                result.out_of_range.append(q_no)
            continue
        if not answer:
            continue
        if q_no in result.answers:
            result.duplicates.setdefault(q_no, [result.answers[q_no]]).append(answer)
        result.answers[q_no] = answer  # oxirgisi kuchga ega

    return result if result.answers else None


def _parse_sequential(text: str, total_q: int) -> ParseResult | None:
    """Raqamsiz javoblar: `a b c d` yoki har qatorda bitta javob."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return None

    tokens: list[str] = []
    if len(lines) == 1:
        parts = [p for p in re.split(r"[\s,;|]+", lines[0]) if p]
        if not all(_LETTERS_ONLY_RE.match(p) for p in parts):
            return None
        tokens = [p.strip(",;.|-") for p in parts]
    else:
        tokens = [_trim_answer(line) for line in lines]

    if not tokens or len(tokens) > total_q:
        return None

    result = ParseResult(mode="sequential")
    for i, token in enumerate(tokens, start=1):
        if token:
            result.answers[i] = token
    return result if result.answers else None


def parse_answers(text: str, total_q: int) -> ParseResult:
    """Matndan javoblarni ajratib oladi. Baholamaydi, faqat o'qiydi."""
    cleaned = _clean(text or "")
    if not cleaned:
        return ParseResult(missing=list(range(1, total_q + 1)))

    result = _parse_numbered(cleaned, total_q) or _parse_sequential(cleaned, total_q)
    if result is None:
        result = ParseResult(missing=list(range(1, total_q + 1)))
        return result

    result.missing = [q for q in range(1, total_q + 1) if q not in result.answers]
    return result


def merge(previous: ParseResult, new: ParseResult, total_q: int) -> ParseResult:
    """Bir necha xabarda kelgan javoblarni birlashtiradi — keyingisi ustun."""
    merged = ParseResult(
        answers={**previous.answers, **new.answers},
        out_of_range=sorted(set(previous.out_of_range) | set(new.out_of_range)),
        duplicates={**previous.duplicates, **new.duplicates},
        mode=new.mode if new.answers else previous.mode,
    )
    merged.missing = [q for q in range(1, total_q + 1) if q not in merged.answers]
    return merged
