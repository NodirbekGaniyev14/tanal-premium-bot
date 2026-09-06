"""Normalizatsiya qoidalarining avtotestlari."""

from __future__ import annotations

import pytest

from app.services.answer_engine.normalize import canon, compare_key, is_match


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        ("  Moon. ", "moon"),
        ("MOON", "moon"),
        ("the moon", "moon"),
        ("A car", "car"),
        ("an apple", "apple"),
        ("car park", "car park"),
        ("fifteen", "15"),
        ("fifteen minutes", "15 minutes"),
        ("twenty five", "25"),
        ("twenty-five", "25"),
        ("T", "true"),
        ("t", "true"),
        ("F", "false"),
        ("NG", "not given"),
        ("not given", "not given"),
        ("NOT GIVEN", "not given"),
        ("Y", "yes"),
    ],
)
def test_canon(given: str, expected: str) -> None:
    assert canon(given) == expected


@pytest.mark.parametrize(
    ("left", "right"),
    [
        ("car park", "carpark"),
        ("car-park", "car park"),
        ("Car Park", "carpark"),
        ("the car park", "car-park"),
        ("15", "fifteen"),
        ("15 minutes", "fifteen minutes"),
        ("NG", "not given"),
        ("t", "TRUE"),
    ],
)
def test_compare_key_equal(left: str, right: str) -> None:
    assert compare_key(left) == compare_key(right)


def test_compare_key_different() -> None:
    assert compare_key("moon") != compare_key("sun")
    assert compare_key("true") != compare_key("false")
    assert compare_key("not given") != compare_key("no")


# --- is_match --------------------------------------------------------------


def test_match_multiple_choice() -> None:
    assert is_match("b", "B")
    assert is_match("B ", "b")
    assert not is_match("c", "B")


def test_variant_a_is_not_treated_as_article() -> None:
    """Variantli javob "A" — artikl emas, u yo'qolmasligi kerak."""
    assert canon("A") == "a"
    assert is_match("a", "A")
    assert not is_match("a", "B")


def test_match_accept_also() -> None:
    assert is_match("15 min", "15 minutes", "fifteen minutes; 15 min")
    assert is_match("fifteen minutes", "15 minutes", "fifteen minutes; 15 min")
    assert is_match("15 minutes", "15 minutes", None)
    assert not is_match("50 minutes", "15 minutes", "fifteen minutes; 15 min")


def test_match_accept_also_pipe_separator() -> None:
    assert is_match("carpark", "car park", "carpark|parking")


def test_empty_answer_never_matches() -> None:
    assert not is_match("", "B")
    assert not is_match("   ", "B")
    assert not is_match("...", "B")
