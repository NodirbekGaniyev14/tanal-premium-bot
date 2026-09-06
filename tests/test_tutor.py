from __future__ import annotations

from app.services.answer_engine.grader import KeyItem, grade
from app.services.tutor import build_advice

KEYS = [
    KeyItem(1, "B", tag="for / since"),
    KeyItem(2, "A", tag="already / yet"),
    KeyItem(3, "D", tag="for / since"),
    KeyItem(4, "C", tag="passive"),
    KeyItem(5, "B", tag="for / since"),
    KeyItem(6, "A", tag="passive"),
]


def test_advice_points_at_dominant_tag() -> None:
    result = grade({1: "a", 2: "a", 3: "b", 4: "c", 5: "a", 6: "a"}, KEYS)
    advice = build_advice(result)
    assert advice is not None
    assert "for / since" in advice
    assert "1, 3, 5" in advice


def test_advice_two_areas() -> None:
    result = grade({1: "a", 2: "a", 3: "b", 4: "a", 5: "b", 6: "b"}, KEYS)
    advice = build_advice(result)
    assert advice is not None
    assert "for / since" in advice
    assert "passive" in advice


def test_advice_when_no_mistakes() -> None:
    result = grade({1: "b", 2: "a", 3: "d", 4: "c", 5: "b", 6: "a"}, KEYS)
    advice = build_advice(result)
    assert advice is not None
    assert "Xatosiz" in advice


def test_advice_without_tags_is_quiet_when_score_is_good() -> None:
    keys = [KeyItem(i, "A") for i in range(1, 11)]
    answers = {i: "A" for i in range(1, 10)}
    result = grade(answers, keys)
    assert build_advice(result) is None
