"""Javob parserining avtotestlari — rejadagi barcha kiritish formatlari."""

from __future__ import annotations

import pytest

from app.services.answer_engine.parser import merge, parse_answers


def _letters(*values: str) -> dict[int, str]:
    return {i: v for i, v in enumerate(values, start=1)}


# --- variantli javoblar, raqam bilan ---------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "1a 2b 3c 4d 5a",
        "1A 2B 3C 4D 5A",
        "1. A  2. B  3. C  4. D  5. A",
        "1) a 2) b 3) c 4) d 5) a",
        "1-A, 2-B, 3-C, 4-D, 5-A",
        "1 - a; 2 - b; 3 - c; 4 - d; 5 - a",
        "1:a 2:b 3:c 4:d 5:a",
        "1.a\n2.b\n3.c\n4.d\n5.a",
        "1) A\n2) B\n3) C\n4) D\n5) A",
        "  1a   2b\n\n 3c  4d 5a  ",
    ],
)
def test_numbered_letter_formats(text: str) -> None:
    result = parse_answers(text, total_q=5)
    assert result.mode == "numbered"
    assert {k: v.lower() for k, v in result.answers.items()} == _letters(
        "a", "b", "c", "d", "a"
    )
    assert result.missing == []


def test_em_dash_and_unicode_spaces() -> None:
    result = parse_answers("1—a 2—b 3—c", total_q=3)
    assert {k: v.lower() for k, v in result.answers.items()} == _letters("a", "b", "c")


# --- raqamsiz, ketma-ket ---------------------------------------------------


@pytest.mark.parametrize(
    "text",
    ["a b c d a", "A B C D A", "a, b, c, d, a", "a;b;c;d;a", "A\nB\nC\nD\nA"],
)
def test_sequential_letters(text: str) -> None:
    result = parse_answers(text, total_q=5)
    assert result.mode == "sequential"
    assert {k: v.lower() for k, v in result.answers.items()} == _letters(
        "a", "b", "c", "d", "a"
    )


# --- so'zli javoblar (reading / listening) ---------------------------------


def test_word_answers_multiline() -> None:
    text = "1) moon\n2) TRUE\n3) 15 minutes\n4) NOT GIVEN"
    result = parse_answers(text, total_q=4)
    assert result.answers == {
        1: "moon",
        2: "TRUE",
        3: "15 minutes",
        4: "NOT GIVEN",
    }


def test_word_answers_single_line() -> None:
    result = parse_answers("1. car park 2. carpark 3. NG", total_q=3)
    assert result.answers == {1: "car park", 2: "carpark", 3: "NG"}


def test_digit_inside_answer_is_not_a_marker() -> None:
    """`15 minutes` javob ichidagi 15 savol raqami sifatida o'qilmasin."""
    result = parse_answers("1. 15 minutes\n2. 20 people", total_q=2)
    assert result.answers == {1: "15 minutes", 2: "20 people"}
    assert result.missing == []


def test_sequential_word_answers_per_line() -> None:
    result = parse_answers("moon\nTRUE\n15 minutes", total_q=3)
    assert result.mode == "sequential"
    assert result.answers == {1: "moon", 2: "TRUE", 3: "15 minutes"}


# --- yetishmayotgan, ortiqcha, takror --------------------------------------


def test_missing_questions_are_reported() -> None:
    result = parse_answers("1a 2b 4d 5a", total_q=5)
    assert result.missing == [3]


def test_out_of_range_numbers() -> None:
    result = parse_answers("1a 2b 99z", total_q=5)
    assert result.out_of_range == [99]
    assert 99 not in result.answers


def test_duplicate_last_wins() -> None:
    result = parse_answers("1a 2b 2c", total_q=3)
    assert result.answers[2] == "c"
    assert result.duplicates[2] == ["b", "c"]


def test_empty_text() -> None:
    result = parse_answers("   ", total_q=4)
    assert result.is_empty
    assert result.missing == [1, 2, 3, 4]


def test_unparseable_text() -> None:
    result = parse_answers("salom ustoz men testni yechdim", total_q=20)
    assert result.is_empty
    assert result.missing == list(range(1, 21))


def test_long_answer_is_trimmed() -> None:
    result = parse_answers("1) " + "x" * 400, total_q=1)
    assert len(result.answers[1]) == 120


# --- bir necha xabarda kelgan javoblar -------------------------------------


def test_merge_across_messages() -> None:
    total = 5
    first = parse_answers("1a 2b 3c", total)
    second = parse_answers("4d 5a", total)
    merged = merge(first, second, total)
    assert {k: v.lower() for k, v in merged.answers.items()} == _letters(
        "a", "b", "c", "d", "a"
    )
    assert merged.missing == []


def test_merge_correction_overrides() -> None:
    total = 3
    first = parse_answers("1a 2b 3c", total)
    fix = parse_answers("2. d", total)
    merged = merge(first, fix, total)
    assert merged.answers[2] == "d"
    assert merged.answers[1] == "a"
