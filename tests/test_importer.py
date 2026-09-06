"""Import qatlamining bazadan mustaqil qismlari: fayl turi va o'qish."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.services.importer import _read_rows, detect_kind
from tools.make_templates import (
    build_ai_tasks,
    build_answer_keys,
    build_levels,
    build_sets,
    build_students,
)


@pytest.mark.parametrize(
    ("file_name", "kind"),
    [
        ("sets.xlsx", "sets"),
        ("answer_keys.xlsx", "answer_keys"),
        ("2026_students.xlsx", "students"),
        ("levels_kuz.xlsx", "levels"),
        ("SETS.XLSX", "sets"),
        ("ai_tasks.xlsx", "ai_tasks"),
    ],
)
def test_detect_kind(file_name: str, kind: str) -> None:
    assert detect_kind(file_name) == kind


def test_detect_kind_unknown() -> None:
    assert detect_kind("mock1.xlsx") is None


def test_templates_are_readable(tmp_path: Path) -> None:
    build_sets(tmp_path / "sets.xlsx")
    build_answer_keys(tmp_path / "answer_keys.xlsx")
    build_levels(tmp_path / "levels.xlsx")
    build_students(tmp_path / "students.xlsx")

    sets_rows = _read_rows((tmp_path / "sets.xlsx").read_bytes())
    assert sets_rows[0]["set_code"] == "GR-T01"
    assert sets_rows[0]["section"] == "grammar_topic"
    assert sets_rows[0]["total_q"] == 20

    keys_rows = _read_rows((tmp_path / "answer_keys.xlsx").read_bytes())
    assert {"set_code", "q_no", "answer", "accept_also", "tag"} <= set(keys_rows[0])

    levels_rows = _read_rows((tmp_path / "levels.xlsx").read_bytes())
    scopes = {row["scope"] for row in levels_rows}
    assert scopes == {"grammar_mock", "reading", "listening"}

    students_rows = _read_rows((tmp_path / "students.xlsx").read_bytes())
    assert students_rows[0]["phone"] == "+998901234567"


def test_ai_tasks_template(tmp_path: Path) -> None:
    build_ai_tasks(tmp_path / "ai_tasks.xlsx")
    rows = _read_rows((tmp_path / "ai_tasks.xlsx").read_bytes())

    kinds = {row["kind"] for row in rows}
    assert kinds == {"writing", "speaking"}

    parts = {row["part"] for row in rows}
    assert {"task1", "task2", "1", "2", "3"} <= {str(p) for p in parts}

    part2 = next(row for row in rows if str(row["part"]) == "2")
    assert part2["cue_points"]  # Part 2 uchun cue card majburiy


def test_read_rows_skips_empty_lines(tmp_path: Path) -> None:
    build_levels(tmp_path / "levels.xlsx")
    rows = _read_rows((tmp_path / "levels.xlsx").read_bytes())
    assert all(row["scope"] for row in rows)
    assert all(row["_row"] >= 2 for row in rows)
