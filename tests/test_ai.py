"""AI qatlamining bazadan va tarmoqdan mustaqil qismlari."""

from __future__ import annotations

import pytest

from app.services.ai.client import AiError, DemoClient, parse_json
from app.services.ai.prompts import speaking_prompt, writing_prompt
from app.services.ai.render import render_speaking, render_writing
from app.services.ai.schemas import (
    SpeakingReview,
    SpeakingScores,
    WritingReview,
    WritingScores,
)
from app.services.ai.service import LimitInfo

# --- sxema -----------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [(6.24, 6.0), (6.25, 6.5), (6.7, 6.5), (6.8, 7.0), (-1.0, 0.0), (12.0, 9.0)],
)
def test_band_rounding(raw: float, expected: float) -> None:
    scores = WritingScores(ta=raw, cc=raw, lr=raw, gra=raw, overall=raw).normalized()
    assert scores.ta == expected


def test_overall_is_computed_when_missing() -> None:
    scores = SpeakingScores(fc=6.0, lr=6.0, gra=7.0, pron=7.0).normalized()
    assert scores.overall == 6.5


# --- JSON parsing ----------------------------------------------------------


def test_parse_plain_json() -> None:
    review = parse_json('{"word_count": 240, "transcript": "hello"}', WritingReview)
    assert review.word_count == 240
    assert review.transcript == "hello"


def test_parse_json_in_code_fence() -> None:
    raw = '```json\n{"insufficient": false, "wpm": 118}\n```'
    review = parse_json(raw, SpeakingReview)
    assert review.wpm == 118


def test_parse_json_with_surrounding_text() -> None:
    raw = 'Mana natija:\n{"word_count": 12}\nRahmat.'
    assert parse_json(raw, WritingReview).word_count == 12


def test_parse_json_missing_fields_uses_defaults() -> None:
    review = parse_json("{}", WritingReview)
    assert review.errors == []
    assert review.scores.overall == 0.0


@pytest.mark.parametrize("raw", ["", "javob yo'q", "{buzuq json"])
def test_parse_json_failures(raw: str) -> None:
    with pytest.raises(AiError):
        parse_json(raw, WritingReview)


# --- promptlar -------------------------------------------------------------


def test_writing_prompt_embeds_task() -> None:
    prompt = writing_prompt("Some people think…", "task_2")
    assert "Some people think…" in prompt
    assert "task_2" in prompt
    assert '"unreadable"' in prompt  # JSON sxemasi buzilmagan


def test_speaking_prompt_embeds_question() -> None:
    prompt = speaking_prompt("Describe a journey", "2")
    assert "Describe a journey" in prompt
    assert "Part 2" in prompt
    assert '"insufficient"' in prompt


# --- demo mijoz ------------------------------------------------------------


async def test_demo_client_writing() -> None:
    result = await DemoClient().generate(prompt="x", parts=[], schema=WritingReview)
    assert result.demo is True
    assert isinstance(result.data, WritingReview)
    assert result.data.errors
    assert result.data.corrected_text


async def test_demo_client_speaking() -> None:
    result = await DemoClient().generate(prompt="x", parts=[], schema=SpeakingReview)
    assert isinstance(result.data, SpeakingReview)
    assert len(result.data.advice) == 3
    assert result.data.model_answer


# --- natija matni ----------------------------------------------------------


def test_render_writing() -> None:
    review = WritingReview(
        word_count=248,
        scores=WritingScores(ta=6.0, cc=6.0, lr=5.5, gra=6.0, overall=6.0),
        errors=[],
        strength="Fikr aniq.",
        fix_first="Artikllar.",
    )
    text = render_writing(review)
    assert "Taxminiy band: 6.0" in text
    assert "LR 5.5" in text
    assert "yakuniy baho o'qituvchiniki" in text
    assert "DEMO" not in text


def test_render_writing_demo_banner() -> None:
    assert "DEMO" in render_writing(WritingReview(), demo=True)


def test_render_writing_escapes_html() -> None:
    review = WritingReview(strength="a < b & c")
    text = render_writing(review)
    assert "a &lt; b &amp; c" in text


def test_render_speaking() -> None:
    review = SpeakingReview(
        transcript="Well, I think…",
        wpm=118,
        long_pauses=4,
        scores=SpeakingScores(fc=6.5, lr=6.0, gra=6.5, pron=7.0, overall=6.5),
        advice=["bir", "ikki", "uch", "to'rt"],
    )
    text = render_speaking(review)
    assert "Taxminiy band: 6.5" in text
    assert "118 so'z/daq" in text
    assert "3. uch" in text
    assert "4. to'rt" not in text  # faqat 3 ta tavsiya ko'rsatiladi


# --- limit -----------------------------------------------------------------


def test_limit_info() -> None:
    assert LimitInfo(used=0, limit=6).allowed
    assert LimitInfo(used=5, limit=6).left == 1
    assert not LimitInfo(used=6, limit=6).allowed
    assert LimitInfo(used=9, limit=6).left == 0
