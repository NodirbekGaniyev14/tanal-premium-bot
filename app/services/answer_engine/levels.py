"""Daraja shkalasi — koddan emas, `levels.xlsx` dan (bazadan) o'qiladi."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class LevelBand:
    scope: str
    raw_min: int
    raw_max: int
    level: str
    label: str | None = None


def pick_level(bands: list[LevelBand], raw_score: int) -> LevelBand | None:
    """Xom ball qaysi darajaga tushishini aniqlaydi."""
    for band in bands:
        if band.raw_min <= raw_score <= band.raw_max:
            return band
    return None


def validate_bands(bands: list[LevelBand]) -> list[str]:
    """Import paytidagi tekshiruv: diapazonlar kesishmasin va uzilmasin."""
    problems: list[str] = []
    ordered = sorted(bands, key=lambda b: b.raw_min)
    for band in ordered:
        if band.raw_max < band.raw_min:
            problems.append(
                f"{band.scope}: {band.raw_min}–{band.raw_max} — yuqori chegara pastdan kichik"
            )
    for prev, nxt in zip(ordered, ordered[1:], strict=False):
        if nxt.raw_min <= prev.raw_max:
            problems.append(
                f"{prev.scope}: {prev.raw_min}–{prev.raw_max} va "
                f"{nxt.raw_min}–{nxt.raw_max} diapazonlari kesishadi"
            )
        elif nxt.raw_min > prev.raw_max + 1:
            problems.append(
                f"{prev.scope}: {prev.raw_max} va {nxt.raw_min} orasida uzilish bor"
            )
    return problems
