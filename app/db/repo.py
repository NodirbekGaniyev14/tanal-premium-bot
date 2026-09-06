"""Baza bilan ishlash — handlerlar SQL yozmaydi, shu yerga murojaat qiladi."""

from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    AiSubmission,
    AiTask,
    AnswerKey,
    Attempt,
    Cohort,
    FileCache,
    Level,
    SetModel,
    Setting,
    Student,
)
from app.enums import FileKind, StudentStatus
from app.services.answer_engine.grader import KeyItem
from app.services.answer_engine.levels import LevelBand

# --- o'quvchilar -----------------------------------------------------------


async def get_student_by_tg(session: AsyncSession, tg_id: int) -> Student | None:
    result = await session.execute(
        select(Student)
        .options(selectinload(Student.cohort))
        .where(Student.tg_id == tg_id)
    )
    return result.scalar_one_or_none()


async def get_student_by_phone(session: AsyncSession, phone: str) -> Student | None:
    result = await session.execute(
        select(Student)
        .options(selectinload(Student.cohort))
        .where(Student.phone == phone)
    )
    return result.scalar_one_or_none()


async def activate_student(
    session: AsyncSession, student: Student, tg_id: int, username: str | None
) -> Student:
    student.tg_id = tg_id
    student.username = username
    student.status = StudentStatus.ACTIVE
    student.activated_at = datetime.now(UTC)
    await session.flush()
    return student


async def touch_last_seen(session: AsyncSession, student_id: int) -> None:
    await session.execute(
        update(Student)
        .where(Student.id == student_id)
        .values(last_seen_at=datetime.now(UTC))
    )


async def get_cohort(session: AsyncSession, name: str) -> Cohort | None:
    result = await session.execute(select(Cohort).where(Cohort.name == name))
    return result.scalar_one_or_none()


async def get_or_create_cohort(session: AsyncSession, name: str) -> Cohort:
    cohort = await get_cohort(session, name)
    if cohort is None:
        cohort = Cohort(name=name)
        session.add(cohort)
        await session.flush()
    return cohort


async def list_cohorts(session: AsyncSession) -> list[Cohort]:
    result = await session.execute(select(Cohort).order_by(Cohort.name))
    return list(result.scalars())


async def list_active_student_tg_ids(
    session: AsyncSession, cohort_id: int | None = None
) -> list[int]:
    query = select(Student.tg_id).where(
        Student.status == StudentStatus.ACTIVE, Student.tg_id.is_not(None)
    )
    if cohort_id is not None:
        query = query.where(Student.cohort_id == cohort_id)
    result = await session.execute(query)
    return [row for row in result.scalars() if row]


# --- to'plamlar ------------------------------------------------------------


async def get_set(session: AsyncSession, set_code: str) -> SetModel | None:
    return await session.get(SetModel, set_code)


async def list_sets(
    session: AsyncSession, section: str, *, only_active: bool = True
) -> list[SetModel]:
    query = select(SetModel).where(SetModel.section == section)
    if only_active:
        query = query.where(SetModel.is_active.is_(True))
    query = query.order_by(SetModel.sort_order, SetModel.set_code)
    result = await session.execute(query)
    return list(result.scalars())


async def list_all_sets(session: AsyncSession) -> list[SetModel]:
    result = await session.execute(
        select(SetModel).order_by(SetModel.section, SetModel.sort_order)
    )
    return list(result.scalars())


async def get_set_by_file_name(session: AsyncSession, file_name: str) -> list[SetModel]:
    """Yuklangan fayl qaysi to'plam(lar)ga tegishli ekanini topadi."""
    result = await session.execute(
        select(SetModel).where(
            (SetModel.pdf_file == file_name)
            | (SetModel.audio_file == file_name)
            | (SetModel.theory_file == file_name)
        )
    )
    return list(result.scalars())


async def get_keys(session: AsyncSession, set_code: str) -> list[KeyItem]:
    result = await session.execute(
        select(AnswerKey).where(AnswerKey.set_code == set_code).order_by(AnswerKey.q_no)
    )
    return [
        KeyItem(q_no=row.q_no, answer=row.answer, accept_also=row.accept_also, tag=row.tag)
        for row in result.scalars()
    ]


async def get_level_bands(session: AsyncSession, scope: str) -> list[LevelBand]:
    result = await session.execute(
        select(Level).where(Level.scope == scope).order_by(Level.raw_min)
    )
    return [
        LevelBand(
            scope=row.scope,
            raw_min=row.raw_min,
            raw_max=row.raw_max,
            level=row.level,
            label=row.label,
        )
        for row in result.scalars()
    ]


# --- urinishlar ------------------------------------------------------------


async def count_attempts(session: AsyncSession, student_id: int, set_code: str) -> int:
    result = await session.execute(
        select(func.count())
        .select_from(Attempt)
        .where(Attempt.student_id == student_id, Attempt.set_code == set_code)
    )
    return int(result.scalar_one())


async def last_attempt(
    session: AsyncSession, student_id: int, set_code: str
) -> Attempt | None:
    result = await session.execute(
        select(Attempt)
        .where(Attempt.student_id == student_id, Attempt.set_code == set_code)
        .order_by(Attempt.attempt_no.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def previous_attempt_in_section(
    session: AsyncSession, student_id: int, section: str, exclude_set: str
) -> Attempt | None:
    """Mocklarni oldingi mock bilan taqqoslash uchun."""
    result = await session.execute(
        select(Attempt)
        .join(SetModel, SetModel.set_code == Attempt.set_code)
        .where(
            Attempt.student_id == student_id,
            SetModel.section == section,
            Attempt.set_code != exclude_set,
        )
        .order_by(Attempt.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def create_attempt(session: AsyncSession, **values: object) -> Attempt:
    attempt = Attempt(**values)  # type: ignore[arg-type]
    session.add(attempt)
    await session.flush()
    return attempt


async def get_attempt(session: AsyncSession, attempt_id: int) -> Attempt | None:
    return await session.get(Attempt, attempt_id)


async def solved_set_codes(session: AsyncSession, student_id: int) -> set[str]:
    result = await session.execute(
        select(Attempt.set_code).where(Attempt.student_id == student_id).distinct()
    )
    return set(result.scalars())


async def best_scores(session: AsyncSession, student_id: int) -> dict[str, tuple[int, int]]:
    """set_code → (eng yaxshi ball, jami)."""
    result = await session.execute(
        select(Attempt.set_code, func.max(Attempt.score), func.max(Attempt.total))
        .where(Attempt.student_id == student_id)
        .group_by(Attempt.set_code)
    )
    return {code: (score, total) for code, score, total in result.all()}


async def student_attempts(
    session: AsyncSession, student_id: int, limit: int = 50
) -> list[Attempt]:
    result = await session.execute(
        select(Attempt)
        .where(Attempt.student_id == student_id)
        .order_by(Attempt.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars())


async def attempts_since(
    session: AsyncSession, student_id: int, since: datetime
) -> list[Attempt]:
    result = await session.execute(
        select(Attempt)
        .where(Attempt.student_id == student_id, Attempt.created_at >= since)
        .order_by(Attempt.created_at)
    )
    return list(result.scalars())


# --- AI topshiriqlari va tekshiruvlari -------------------------------------


async def list_ai_tasks(
    session: AsyncSession, kind: str, part: str | None = None
) -> list[AiTask]:
    query = select(AiTask).where(AiTask.kind == kind, AiTask.is_active.is_(True))
    if part is not None:
        query = query.where(AiTask.part == part)
    result = await session.execute(query.order_by(AiTask.code))
    return list(result.scalars())


async def list_ai_parts(session: AsyncSession, kind: str) -> list[str]:
    result = await session.execute(
        select(AiTask.part)
        .where(AiTask.kind == kind, AiTask.is_active.is_(True), AiTask.part.is_not(None))
        .distinct()
        .order_by(AiTask.part)
    )
    return [part for part in result.scalars() if part]


async def get_ai_task(session: AsyncSession, task_id: int) -> AiTask | None:
    return await session.get(AiTask, task_id)


async def get_ai_task_by_file_name(
    session: AsyncSession, file_name: str
) -> list[AiTask]:
    result = await session.execute(
        select(AiTask).where(AiTask.image_file == file_name)
    )
    return list(result.scalars())


async def count_ai_today(session: AsyncSession, student_id: int) -> int:
    since = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    result = await session.execute(
        select(func.count())
        .select_from(AiSubmission)
        .where(
            AiSubmission.student_id == student_id,
            AiSubmission.created_at >= since,
            AiSubmission.status == "done",
        )
    )
    return int(result.scalar_one())


async def create_ai_submission(session: AsyncSession, **values: object) -> AiSubmission:
    submission = AiSubmission(**values)  # type: ignore[arg-type]
    session.add(submission)
    await session.flush()
    return submission


async def get_ai_submission(
    session: AsyncSession, submission_id: int
) -> AiSubmission | None:
    return await session.get(AiSubmission, submission_id)


async def last_ai_submission(
    session: AsyncSession, student_id: int, kind: str
) -> AiSubmission | None:
    result = await session.execute(
        select(AiSubmission)
        .where(AiSubmission.student_id == student_id, AiSubmission.kind == kind)
        .order_by(AiSubmission.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


# --- fayl keshi ------------------------------------------------------------


async def get_cached_file(
    session: AsyncSession, student_id: int, set_code: str, kind: FileKind | str
) -> str | None:
    result = await session.execute(
        select(FileCache.file_id).where(
            FileCache.student_id == student_id,
            FileCache.set_code == set_code,
            FileCache.kind == str(kind),
        )
    )
    return result.scalar_one_or_none()


async def cache_file(
    session: AsyncSession,
    student_id: int,
    set_code: str,
    kind: FileKind | str,
    file_id: str,
) -> None:
    session.add(
        FileCache(
            student_id=student_id, set_code=set_code, kind=str(kind), file_id=file_id
        )
    )
    await session.flush()


async def drop_cached_files(session: AsyncSession, set_code: str) -> None:
    """Fayl yangilanganda eski ism yozilgan nusxalar kuchini yo'qotadi."""
    await session.execute(delete(FileCache).where(FileCache.set_code == set_code))


# --- sozlamalar ------------------------------------------------------------


async def get_setting(
    session: AsyncSession, key: str, default: str | None = None
) -> str | None:
    row = await session.get(Setting, key)
    return row.value if row else default


async def set_setting(session: AsyncSession, key: str, value: str) -> None:
    row = await session.get(Setting, key)
    if row:
        row.value = value
    else:
        session.add(Setting(key=key, value=value))
    await session.flush()


# --- kirish nazorati -------------------------------------------------------


def access_expired(student: Student, today: date | None = None) -> bool:
    today = today or date.today()
    if student.access_until and student.access_until < today:
        return True
    cohort = student.cohort
    return bool(cohort and cohort.ends_at and cohort.ends_at < today)
