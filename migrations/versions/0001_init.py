"""boshlang'ich sxema — 10 jadval

Revision ID: 0001_init
Revises:
Create Date: 2026-09-06
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cohorts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(64), nullable=False, unique=True),
        sa.Column("starts_at", sa.Date()),
        sa.Column("ends_at", sa.Date()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_cohorts_name", "cohorts", ["name"])

    op.create_table(
        "students",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tg_id", sa.BigInteger(), unique=True),
        sa.Column("phone", sa.String(20), nullable=False, unique=True),
        sa.Column("full_name", sa.String(128), nullable=False),
        sa.Column("username", sa.String(64)),
        sa.Column(
            "cohort_id",
            sa.Integer(),
            sa.ForeignKey("cohorts.id", ondelete="SET NULL"),
        ),
        sa.Column("status", sa.String(16), nullable=False, server_default="invited"),
        sa.Column("access_until", sa.Date()),
        sa.Column("note", sa.Text()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("activated_at", sa.DateTime(timezone=True)),
        sa.Column("last_seen_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_students_tg_id", "students", ["tg_id"])
    op.create_index("ix_students_phone", "students", ["phone"])
    op.create_index("ix_students_cohort_id", "students", ["cohort_id"])

    op.create_table(
        "sets",
        sa.Column("set_code", sa.String(32), primary_key=True),
        sa.Column("section", sa.String(32), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("topic_no", sa.Integer()),
        sa.Column("total_q", sa.Integer(), nullable=False),
        sa.Column("attempts_allowed", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("reveal", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("requires", sa.String(32)),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pdf_file", sa.String(160)),
        sa.Column("audio_file", sa.String(160)),
        sa.Column("theory_file", sa.String(160)),
        sa.Column("pdf_file_id", sa.String(256)),
        sa.Column("audio_file_id", sa.String(256)),
        sa.Column("theory_file_id", sa.String(256)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("total_q > 0", name="ck_sets_total_q_positive"),
        sa.CheckConstraint("attempts_allowed > 0", name="ck_sets_attempts_positive"),
    )
    op.create_index("ix_sets_section", "sets", ["section"])
    op.create_index("ix_sets_section_sort", "sets", ["section", "sort_order"])

    op.create_table(
        "answer_keys",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "set_code",
            sa.String(32),
            sa.ForeignKey("sets.set_code", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("q_no", sa.Integer(), nullable=False),
        sa.Column("answer", sa.String(160), nullable=False),
        sa.Column("accept_also", sa.String(320)),
        sa.Column("tag", sa.String(80)),
        sa.UniqueConstraint("set_code", "q_no", name="uq_answer_keys_set_qno"),
        sa.CheckConstraint("q_no > 0", name="ck_answer_keys_qno_positive"),
    )
    op.create_index("ix_answer_keys_set_code", "answer_keys", ["set_code"])
    op.create_index("ix_answer_keys_tag", "answer_keys", ["tag"])

    op.create_table(
        "levels",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("scope", sa.String(32), nullable=False),
        sa.Column("raw_min", sa.Integer(), nullable=False),
        sa.Column("raw_max", sa.Integer(), nullable=False),
        sa.Column("level", sa.String(16), nullable=False),
        sa.Column("label", sa.String(64)),
        sa.UniqueConstraint("scope", "raw_min", name="uq_levels_scope_min"),
        sa.CheckConstraint("raw_max >= raw_min", name="ck_levels_range"),
    )
    op.create_index("ix_levels_scope", "levels", ["scope"])

    op.create_table(
        "attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "student_id",
            sa.Integer(),
            sa.ForeignKey("students.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "set_code",
            sa.String(32),
            sa.ForeignKey("sets.set_code", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("attempt_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("submitted_raw", sa.Text(), nullable=False),
        sa.Column("parsed", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("total", sa.Integer(), nullable=False),
        sa.Column("level", sa.String(16)),
        sa.Column("level_label", sa.String(64)),
        sa.Column("wrong_nos", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("weak_tags", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "student_id", "set_code", "attempt_no", name="uq_attempts_student_set_no"
        ),
    )
    op.create_index("ix_attempts_student_id", "attempts", ["student_id"])
    op.create_index("ix_attempts_set_code", "attempts", ["set_code"])
    op.create_index("ix_attempts_created_at", "attempts", ["created_at"])
    op.create_index("ix_attempts_student_created", "attempts", ["student_id", "created_at"])

    op.create_table(
        "file_cache",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "student_id",
            sa.Integer(),
            sa.ForeignKey("students.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "set_code",
            sa.String(32),
            sa.ForeignKey("sets.set_code", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(16), nullable=False, server_default="pdf"),
        sa.Column("file_id", sa.String(256), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "student_id", "set_code", "kind", name="uq_file_cache_student_set_kind"
        ),
    )
    op.create_index("ix_file_cache_student_id", "file_cache", ["student_id"])
    op.create_index("ix_file_cache_set_code", "file_cache", ["set_code"])

    op.create_table(
        "ai_tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(32), nullable=False, unique=True),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("part", sa.String(16)),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("prompt_text", sa.Text(), nullable=False),
        sa.Column("cue_points", sa.Text()),
        sa.Column("image_file", sa.String(160)),
        sa.Column("image_file_id", sa.String(256)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.create_index("ix_ai_tasks_code", "ai_tasks", ["code"])
    op.create_index("ix_ai_tasks_kind", "ai_tasks", ["kind"])

    op.create_table(
        "ai_submissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "student_id",
            sa.Integer(),
            sa.ForeignKey("students.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "task_id", sa.Integer(), sa.ForeignKey("ai_tasks.id", ondelete="SET NULL")
        ),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column(
            "input_file_ids", postgresql.JSONB(), nullable=False, server_default="[]"
        ),
        sa.Column("transcript", sa.Text()),
        sa.Column("model", sa.String(64)),
        sa.Column("prompt_version", sa.String(32)),
        sa.Column("scores", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("overall", sa.Numeric(3, 1)),
        sa.Column("feedback", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("tokens_in", sa.Integer()),
        sa.Column("tokens_out", sa.Integer()),
        sa.Column("status", sa.String(16), nullable=False, server_default="done"),
        sa.Column("error", sa.Text()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_ai_submissions_student_id", "ai_submissions", ["student_id"])
    op.create_index("ix_ai_submissions_kind", "ai_submissions", ["kind"])
    op.create_index("ix_ai_submissions_created_at", "ai_submissions", ["created_at"])

    op.create_table(
        "settings",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    for table in (
        "settings",
        "ai_submissions",
        "ai_tasks",
        "file_cache",
        "attempts",
        "levels",
        "answer_keys",
        "sets",
        "students",
        "cohorts",
    ):
        op.drop_table(table)
