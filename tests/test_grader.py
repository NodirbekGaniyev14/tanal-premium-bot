"""Baholash va daraja aniqlashning avtotestlari."""

from __future__ import annotations

from app.services.answer_engine.grader import KeyItem, grade
from app.services.answer_engine.levels import LevelBand, pick_level, validate_bands
from app.services.answer_engine.parser import parse_answers

KEYS = [
    KeyItem(1, "B", tag="for / since"),
    KeyItem(2, "A", tag="already / yet"),
    KeyItem(3, "D", tag="for / since"),
    KeyItem(4, "C", tag="passive"),
    KeyItem(5, "B", tag="for / since"),
]


def test_all_correct() -> None:
    result = grade({1: "b", 2: "a", 3: "d", 4: "c", 5: "b"}, KEYS)
    assert result.score == 5
    assert result.total == 5
    assert result.percent == 100
    assert result.wrong_nos == []
    assert result.weak_tags == {}


def test_partial_and_weak_tags() -> None:
    result = grade({1: "a", 2: "a", 3: "b", 4: "c", 5: "a"}, KEYS)
    assert result.score == 2
    assert result.wrong_nos == [1, 3, 5]
    assert result.weak_tags == {"for / since": 3}
    assert result.tag_totals["for / since"] == 3


def test_unanswered_counts_as_wrong() -> None:
    result = grade({1: "b", 2: "a"}, KEYS)
    assert result.score == 2
    assert result.wrong_nos == [3, 4, 5]
    assert result.unanswered_nos == [3, 4, 5]


def test_word_answers_with_accept_also() -> None:
    keys = [
        KeyItem(1, "car park", "carpark", tag="matching"),
        KeyItem(2, "TRUE", "T", tag="true/false"),
        KeyItem(3, "15 minutes", "fifteen minutes; 15 min", tag="form filling"),
    ]
    answers = parse_answers("1) the Car-Park\n2) t\n3) fifteen minutes", total_q=3)
    result = grade(answers.answers, keys)
    assert result.score == 3
    assert result.wrong_nos == []


def test_percent_rounding() -> None:
    keys = [KeyItem(i, "A") for i in range(1, 21)]
    result = grade({i: "A" for i in range(1, 17)}, keys)
    assert result.score == 16
    assert result.percent == 80


# --- daraja ----------------------------------------------------------------

BANDS = [
    LevelBand("grammar_mock", 0, 15, "A1", "Beginner"),
    LevelBand("grammar_mock", 16, 25, "A2", "Elementary"),
    LevelBand("grammar_mock", 26, 35, "B1", "Intermediate"),
    LevelBand("grammar_mock", 36, 44, "B2", "Upper-Intermediate"),
    LevelBand("grammar_mock", 45, 50, "C1", "Advanced"),
]


def test_pick_level() -> None:
    assert pick_level(BANDS, 34).level == "B1"
    assert pick_level(BANDS, 0).level == "A1"
    assert pick_level(BANDS, 50).level == "C1"
    assert pick_level(BANDS, 51) is None


def test_validate_bands_ok() -> None:
    assert validate_bands(BANDS) == []


def test_validate_bands_overlap() -> None:
    broken = [
        LevelBand("reading", 0, 20, "A1"),
        LevelBand("reading", 18, 30, "A2"),
    ]
    assert any("kesishadi" in p for p in validate_bands(broken))


def test_validate_bands_gap() -> None:
    broken = [
        LevelBand("reading", 0, 20, "A1"),
        LevelBand("reading", 25, 30, "A2"),
    ]
    assert any("uzilish" in p for p in validate_bands(broken))
