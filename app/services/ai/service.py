"""AI tekshiruvining yuqori qatlami: limit → so'rov → baza → natija."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import repo
from app.db.models import AiSubmission, AiTask, Student
from app.enums import AiKind
from app.services.ai.client import AiError, MediaPart, get_client
from app.services.ai.prompts import (
    SPEAKING_PROMPT_VERSION,
    WRITING_PROMPT_VERSION,
    speaking_prompt,
    writing_prompt,
)
from app.services.ai.schemas import SpeakingReview, WritingReview

logger = logging.getLogger(__name__)

#: Kunlik limitni bazadan ham o'zgartirish mumkin (`settings` jadvali).
DAILY_LIMIT_KEY = "ai_daily_limit"


@dataclass(slots=True, frozen=True)
class LimitInfo:
    used: int
    limit: int

    @property
    def allowed(self) -> bool:
        return self.used < self.limit

    @property
    def left(self) -> int:
        return max(0, self.limit - self.used)


@dataclass(slots=True)
class ReviewOutcome:
    submission: AiSubmission
    review: WritingReview | SpeakingReview | None
    demo: bool
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.review is not None and self.error is None


async def daily_limit(session: AsyncSession) -> int:
    raw = await repo.get_setting(session, DAILY_LIMIT_KEY)
    if raw and raw.strip().isdigit():
        return int(raw.strip())
    return get_settings().ai_daily_limit


async def check_limit(session: AsyncSession, student: Student) -> LimitInfo:
    return LimitInfo(
        used=await repo.count_ai_today(session, student.id),
        limit=await daily_limit(session),
    )


async def _run(
    session: AsyncSession,
    *,
    student: Student,
    task: AiTask | None,
    kind: AiKind,
    prompt: str,
    prompt_version: str,
    parts: list[MediaPart],
    file_ids: list[str],
    schema: type[WritingReview] | type[SpeakingReview],
) -> ReviewOutcome:
    client = get_client()
    base = {
        "student_id": student.id,
        "task_id": task.id if task else None,
        "kind": str(kind),
        "input_file_ids": file_ids,
        "prompt_version": prompt_version,
    }

    try:
        result = await client.generate(prompt=prompt, parts=parts, schema=schema)
    except AiError as exc:
        logger.warning("AI tekshiruvi muvaffaqiyatsiz: %s", exc)
        submission = await repo.create_ai_submission(
            session,
            **base,
            model=client.model_name,
            status="error",
            error=str(exc)[:2000],
        )
        return ReviewOutcome(submission=submission, review=None, demo=False, error=str(exc))

    review = result.data
    scores = review.scores.normalized().model_dump()
    transcript = getattr(review, "transcript", "") or ""

    feedback = review.model_dump(exclude={"scores", "transcript"})
    submission = await repo.create_ai_submission(
        session,
        **base,
        model=result.model,
        transcript=transcript,
        scores=scores,
        overall=scores.get("overall"),
        feedback=feedback,
        tokens_in=result.tokens_in,
        tokens_out=result.tokens_out,
        status="done",
    )
    return ReviewOutcome(submission=submission, review=review, demo=result.demo)


async def review_writing(
    session: AsyncSession,
    *,
    student: Student,
    task: AiTask | None,
    task_prompt: str,
    task_type: str,
    images: list[MediaPart],
    file_ids: list[str],
) -> ReviewOutcome:
    return await _run(
        session,
        student=student,
        task=task,
        kind=AiKind.WRITING,
        prompt=writing_prompt(task_prompt, task_type),
        prompt_version=WRITING_PROMPT_VERSION,
        parts=images,
        file_ids=file_ids,
        schema=WritingReview,
    )


async def review_speaking(
    session: AsyncSession,
    *,
    student: Student,
    task: AiTask | None,
    question: str,
    part: str,
    audio: MediaPart,
    file_ids: list[str],
) -> ReviewOutcome:
    return await _run(
        session,
        student=student,
        task=task,
        kind=AiKind.SPEAKING,
        prompt=speaking_prompt(question, part),
        prompt_version=SPEAKING_PROMPT_VERSION,
        parts=[audio],
        file_ids=file_ids,
        schema=SpeakingReview,
    )
