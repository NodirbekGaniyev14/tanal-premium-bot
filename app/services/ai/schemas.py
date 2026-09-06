"""Gemini javobining sxemasi.

Erkin matnni parse qilish doimiy sinish manbai — shuning uchun model
faqat shu sxema bo'yicha JSON qaytaradi va javob pydantic bilan tekshiriladi.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from pydantic import BaseModel, Field


def _band(value: float) -> float:
    """IELTS band 0–9, 0.5 qadam bilan.

    Python `round()` bank yaxlitlashini qiladi (6.25 → 6.0), imtihon esa
    yuqoriga yaxlitlaydi — shuning uchun aniq ROUND_HALF_UP.
    """
    clamped = max(0.0, min(9.0, float(value)))
    halves = Decimal(str(clamped * 2)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return float(halves) / 2


class WritingScores(BaseModel):
    ta: float = 0.0
    cc: float = 0.0
    lr: float = 0.0
    gra: float = 0.0
    overall: float = 0.0

    def normalized(self) -> WritingScores:
        return WritingScores(
            ta=_band(self.ta),
            cc=_band(self.cc),
            lr=_band(self.lr),
            gra=_band(self.gra),
            overall=_band(self.overall or (self.ta + self.cc + self.lr + self.gra) / 4),
        )


class WritingError(BaseModel):
    no: int = 0
    original: str = ""
    correction: str = ""
    why: str = ""


class WritingReview(BaseModel):
    unreadable: bool = False
    word_count: int = 0
    transcript: str = ""
    scores: WritingScores = Field(default_factory=WritingScores)
    errors: list[WritingError] = Field(default_factory=list)
    error_count_total: int = 0
    strength: str = ""
    fix_first: str = ""
    corrected_text: str = ""


class SpeakingScores(BaseModel):
    fc: float = 0.0
    lr: float = 0.0
    gra: float = 0.0
    pron: float = 0.0
    overall: float = 0.0

    def normalized(self) -> SpeakingScores:
        return SpeakingScores(
            fc=_band(self.fc),
            lr=_band(self.lr),
            gra=_band(self.gra),
            pron=_band(self.pron),
            overall=_band(
                self.overall or (self.fc + self.lr + self.gra + self.pron) / 4
            ),
        )


class GrammarError(BaseModel):
    quote: str = ""
    correction: str = ""


class SpeakingReview(BaseModel):
    insufficient: bool = False
    transcript: str = ""
    duration_sec: int = 0
    wpm: int = 0
    long_pauses: int = 0
    scores: SpeakingScores = Field(default_factory=SpeakingScores)
    grammar_errors: list[GrammarError] = Field(default_factory=list)
    advice: list[str] = Field(default_factory=list)
    model_answer: str = ""
