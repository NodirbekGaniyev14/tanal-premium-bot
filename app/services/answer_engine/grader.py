"""Baholash: o'qilgan javoblarni kalit bilan solishtirish."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from app.services.answer_engine.normalize import is_match


@dataclass(slots=True, frozen=True)
class KeyItem:
    q_no: int
    answer: str
    accept_also: str | None = None
    tag: str | None = None


@dataclass(slots=True, frozen=True)
class QuestionResult:
    q_no: int
    given: str
    expected: str
    correct: bool
    tag: str | None = None

    @property
    def answered(self) -> bool:
        return bool(self.given)


@dataclass(slots=True)
class GradeResult:
    score: int = 0
    total: int = 0
    results: list[QuestionResult] = field(default_factory=list)
    wrong_nos: list[int] = field(default_factory=list)
    unanswered_nos: list[int] = field(default_factory=list)
    #: tag → shu tag bo'yicha xatolar soni (ko'pdan kamga)
    weak_tags: dict[str, int] = field(default_factory=dict)
    #: tag → shu tag bo'yicha jami savollar soni
    tag_totals: dict[str, int] = field(default_factory=dict)

    @property
    def percent(self) -> int:
        return round(self.score * 100 / self.total) if self.total else 0


def grade(answers: dict[int, str], keys: list[KeyItem]) -> GradeResult:
    """`answers` — savol raqami → o'quvchi javobi. `keys` — javob kaliti."""
    result = GradeResult(total=len(keys))
    wrong_tags: Counter[str] = Counter()
    tag_totals: Counter[str] = Counter()

    for key in sorted(keys, key=lambda k: k.q_no):
        given = (answers.get(key.q_no) or "").strip()
        correct = is_match(given, key.answer, key.accept_also)
        result.results.append(
            QuestionResult(
                q_no=key.q_no,
                given=given,
                expected=key.answer,
                correct=correct,
                tag=key.tag,
            )
        )
        if key.tag:
            tag_totals[key.tag] += 1
        if correct:
            result.score += 1
        else:
            result.wrong_nos.append(key.q_no)
            if not given:
                result.unanswered_nos.append(key.q_no)
            if key.tag:
                wrong_tags[key.tag] += 1

    result.weak_tags = dict(wrong_tags.most_common())
    result.tag_totals = dict(tag_totals)
    return result
