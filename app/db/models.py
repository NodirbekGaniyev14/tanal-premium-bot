"""Rejadagi 10 jadval.

Excel — haqiqat manbai: `sets`, `answer_keys`, `levels`, `students` jadvallari
import orqali to'ldiriladi, qo'lda tahrirlanmaydi.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.enums import AiKind, FileKind, Section, StudentStatus


class Cohort(Base):
    """Kurs oqimi: `2026-kuz`, `2027-bahor`."""

    __tablename__ = "cohorts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    starts_at: Mapped[date | None] = mapped_column(Date)
    ends_at: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    students: Mapped[list[Student]] = relationship(back_populates="cohort")


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tg_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(128))
    username: Mapped[str | None] = mapped_column(String(64))
    cohort_id: Mapped[int | None] = mapped_column(
        ForeignKey("cohorts.id", ondelete="SET NULL"), index=True
    )
    status: Mapped[str] = mapped_column(
        String(16), default=StudentStatus.INVITED, server_default=StudentStatus.INVITED
    )
    access_until: Mapped[date | None] = mapped_column(Date)
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    cohort: Mapped[Cohort | None] = relationship(back_populates="students")
    attempts: Mapped[list[Attempt]] = relationship(back_populates="student")


class SetModel(Base):
    """Har bir test yoki mockning pasporti. `sets.xlsx` dan keladi."""

    __tablename__ = "sets"

    set_code: Mapped[str] = mapped_column(String(32), primary_key=True)
    section: Mapped[str] = mapped_column(String(32), index=True)
    title: Mapped[str] = mapped_column(String(160))
    topic_no: Mapped[int | None] = mapped_column(Integer)
    total_q: Mapped[int] = mapped_column(Integer)
    attempts_allowed: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    reveal: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    requires: Mapped[str | None] = mapped_column(String(32))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    pdf_file: Mapped[str | None] = mapped_column(String(160))
    audio_file: Mapped[str | None] = mapped_column(String(160))
    theory_file: Mapped[str | None] = mapped_column(String(160))

    pdf_file_id: Mapped[str | None] = mapped_column(String(256))
    audio_file_id: Mapped[str | None] = mapped_column(String(256))
    theory_file_id: Mapped[str | None] = mapped_column(String(256))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint("total_q > 0", name="ck_sets_total_q_positive"),
        CheckConstraint("attempts_allowed > 0", name="ck_sets_attempts_positive"),
        Index("ix_sets_section_sort", "section", "sort_order"),
    )

    keys: Mapped[list[AnswerKey]] = relationship(
        back_populates="set", cascade="all, delete-orphan"
    )

    @property
    def section_enum(self) -> Section:
        return Section(self.section)


class AnswerKey(Base):
    """Javob kaliti. Baholash ham, tavsiya ham shundan."""

    __tablename__ = "answer_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    set_code: Mapped[str] = mapped_column(
        ForeignKey("sets.set_code", ondelete="CASCADE"), index=True
    )
    q_no: Mapped[int] = mapped_column(Integer)
    answer: Mapped[str] = mapped_column(String(160))
    accept_also: Mapped[str | None] = mapped_column(String(320))
    tag: Mapped[str | None] = mapped_column(String(80), index=True)

    __table_args__ = (
        UniqueConstraint("set_code", "q_no", name="uq_answer_keys_set_qno"),
        CheckConstraint("q_no > 0", name="ck_answer_keys_qno_positive"),
    )

    set: Mapped[SetModel] = relationship(back_populates="keys")


class Level(Base):
    """Daraja shkalasi — koddan emas, bazadan o'qiladi."""

    __tablename__ = "levels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scope: Mapped[str] = mapped_column(String(32), index=True)
    raw_min: Mapped[int] = mapped_column(Integer)
    raw_max: Mapped[int] = mapped_column(Integer)
    level: Mapped[str] = mapped_column(String(16))
    label: Mapped[str | None] = mapped_column(String(64))

    __table_args__ = (
        UniqueConstraint("scope", "raw_min", name="uq_levels_scope_min"),
        CheckConstraint("raw_max >= raw_min", name="ck_levels_range"),
    )


class Attempt(Base):
    """Har urinish. Butun statistika va tavsiyalar shu jadvaldan."""

    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), index=True
    )
    set_code: Mapped[str] = mapped_column(
        ForeignKey("sets.set_code", ondelete="CASCADE"), index=True
    )
    attempt_no: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    submitted_raw: Mapped[str] = mapped_column(Text)
    parsed: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    score: Mapped[int] = mapped_column(Integer)
    total: Mapped[int] = mapped_column(Integer)
    level: Mapped[str | None] = mapped_column(String(16))
    level_label: Mapped[str | None] = mapped_column(String(64))
    wrong_nos: Mapped[list[int]] = mapped_column(JSONB, default=list)
    weak_tags: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    __table_args__ = (
        UniqueConstraint(
            "student_id", "set_code", "attempt_no", name="uq_attempts_student_set_no"
        ),
        Index("ix_attempts_student_created", "student_id", "created_at"),
    )

    student: Mapped[Student] = relationship(back_populates="attempts")


class FileCache(Base):
    """Ism yozilgan PDF nusxalari — bir marta yaratiladi, keyin qayta ishlatiladi."""

    __tablename__ = "file_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), index=True
    )
    set_code: Mapped[str] = mapped_column(
        ForeignKey("sets.set_code", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(16), default=FileKind.PDF)
    file_id: Mapped[str] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "student_id", "set_code", "kind", name="uq_file_cache_student_set_kind"
        ),
    )


class AiTask(Base):
    """Speaking savollari va writing topshiriqlari banki."""

    __tablename__ = "ai_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    kind: Mapped[str] = mapped_column(String(16), index=True)  # AiKind
    part: Mapped[str | None] = mapped_column(String(16))  # task1/task2 | 1/2/3
    title: Mapped[str] = mapped_column(String(160))
    prompt_text: Mapped[str] = mapped_column(Text)
    cue_points: Mapped[str | None] = mapped_column(Text)
    image_file: Mapped[str | None] = mapped_column(String(160))
    image_file_id: Mapped[str | None] = mapped_column(String(256))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    @property
    def kind_enum(self) -> AiKind:
        return AiKind(self.kind)


class AiSubmission(Base):
    """Writing va speaking tekshiruvlari. Xarajat hisobi ham shu yerdan."""

    __tablename__ = "ai_submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), index=True
    )
    task_id: Mapped[int | None] = mapped_column(
        ForeignKey("ai_tasks.id", ondelete="SET NULL")
    )
    kind: Mapped[str] = mapped_column(String(16), index=True)
    input_file_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)
    transcript: Mapped[str | None] = mapped_column(Text)
    model: Mapped[str | None] = mapped_column(String(64))
    prompt_version: Mapped[str | None] = mapped_column(String(32))
    scores: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    overall: Mapped[float | None] = mapped_column(Numeric(3, 1))
    feedback: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    tokens_in: Mapped[int | None] = mapped_column(Integer)
    tokens_out: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16), default="done", server_default="done")
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class Setting(Base):
    """Kunlik AI limiti, matnlar, texnik tanaffus rejimi."""

    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
