"""Demo kontent: kontent va API kaliti yo'q holatda ham botni to'liq sinash.

Bu yerdagi hamma narsa vaqtinchalik namuna. Haqiqiy kontent kelganda
`sets.xlsx` / `answer_keys.xlsx` importi bir xil kodlar bilan ustiga yozadi
yoki demo yozuvlarini o'chirib tashlaysiz (`is_active = false`).
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import repo
from app.db.models import AiTask, AnswerKey, Level, SetModel, Student
from app.enums import AiKind, Section, StudentStatus
from app.utils.phone import normalize_phone

DEMO_COHORT = "demo"

_SETS: list[dict[str, object]] = [
    {
        "set_code": "DEMO-GR-T01",
        "section": Section.GRAMMAR_TOPIC.value,
        "title": "DEMO 1. Articles — test",
        "topic_no": 1,
        "total_q": 10,
        "attempts_allowed": 3,
        "reveal": True,
        "sort_order": 1,
    },
    {
        "set_code": "DEMO-GR-M01",
        "section": Section.GRAMMAR_MOCK.value,
        "title": "DEMO Grammatika mock 1",
        "total_q": 20,
        "attempts_allowed": 1,
        "reveal": False,
        "sort_order": 1,
    },
    {
        "set_code": "DEMO-RD-M01",
        "section": Section.READING.value,
        "title": "DEMO Reading mock 1",
        "total_q": 8,
        "attempts_allowed": 1,
        "reveal": False,
        "sort_order": 1,
    },
]

#: (q_no, answer, accept_also, tag)
_KEYS: dict[str, list[tuple[int, str, str | None, str | None]]] = {
    "DEMO-GR-T01": [
        (1, "B", None, "a / an"),
        (2, "A", None, "a / an"),
        (3, "C", None, "the"),
        (4, "D", None, "the"),
        (5, "B", None, "zero article"),
        (6, "A", None, "zero article"),
        (7, "C", None, "the"),
        (8, "B", None, "a / an"),
        (9, "D", None, "zero article"),
        (10, "A", None, "the"),
    ],
    "DEMO-RD-M01": [
        (1, "moon", None, "matching"),
        (2, "TRUE", "T", "true/false"),
        (3, "NOT GIVEN", "NG", "true/false"),
        (4, "car park", "carpark", "matching"),
        (5, "15 minutes", "fifteen minutes; 15 min", "form filling"),
        (6, "FALSE", "F", "true/false"),
        (7, "the library", "library", "matching"),
        (8, "twenty five", "25", "form filling"),
    ],
}


def _mock_keys() -> list[tuple[int, str, str | None, str | None]]:
    """20 savollik demo mock: javoblar A→D aylanadi, teglar takrorlanadi."""
    letters = "ABCD"
    tags = ["conditionals", "passive", "tenses", "articles"]
    return [
        (index, letters[index % 4], None, tags[(index // 2) % 4])
        for index in range(1, 21)
    ]


_LEVELS: dict[str, list[tuple[int, int, str, str]]] = {
    Section.GRAMMAR_MOCK.value: [
        (0, 6, "A1", "Beginner"),
        (7, 10, "A2", "Elementary"),
        (11, 14, "B1", "Intermediate"),
        (15, 17, "B2", "Upper-Intermediate"),
        (18, 20, "C1", "Advanced"),
    ],
    Section.READING.value: [
        (0, 2, "A1", "Beginner"),
        (3, 4, "A2", "Elementary"),
        (5, 6, "B1", "Intermediate"),
        (7, 7, "B2", "Upper-Intermediate"),
        (8, 8, "C1", "Advanced"),
    ],
}

_AI_TASKS: list[dict[str, object]] = [
    {
        "code": "DEMO-WR-T1-01",
        "kind": AiKind.WRITING.value,
        "part": "task1",
        "title": "DEMO Task 1 — chiziqli grafik",
        "prompt_text": (
            "The graph below shows the number of visitors to three museums in "
            "London between 2007 and 2012. Summarise the information by selecting "
            "and reporting the main features, and make comparisons where relevant. "
            "Write at least 150 words."
        ),
    },
    {
        "code": "DEMO-WR-T2-01",
        "kind": AiKind.WRITING.value,
        "part": "task2",
        "title": "DEMO Task 2 — ta'lim",
        "prompt_text": (
            "Some people think that universities should provide graduates with the "
            "knowledge and skills needed in the workplace. Others think that the "
            "true function of a university is to give access to knowledge for its "
            "own sake. Discuss both views and give your own opinion. "
            "Write at least 250 words."
        ),
    },
    {
        "code": "DEMO-SP-P1-01",
        "kind": AiKind.SPEAKING.value,
        "part": "1",
        "title": "DEMO Part 1 — uy",
        "prompt_text": (
            "Let's talk about your home. Do you live in a house or an apartment? "
            "What do you like most about the place where you live?"
        ),
    },
    {
        "code": "DEMO-SP-P1-02",
        "kind": AiKind.SPEAKING.value,
        "part": "1",
        "title": "DEMO Part 1 — ish va o'qish",
        "prompt_text": (
            "Do you work or are you a student? Why did you choose that job "
            "or subject?"
        ),
    },
    {
        "code": "DEMO-SP-P2-01",
        "kind": AiKind.SPEAKING.value,
        "part": "2",
        "title": "DEMO Part 2 — sayohat",
        "prompt_text": "Describe a journey that you remember well.",
        "cue_points": (
            "You should say:\n"
            "— where you went\n"
            "— who you went with\n"
            "— what you did there\n"
            "and explain why you remember this journey well."
        ),
    },
    {
        "code": "DEMO-SP-P3-01",
        "kind": AiKind.SPEAKING.value,
        "part": "3",
        "title": "DEMO Part 3 — sayohat va jamiyat",
        "prompt_text": (
            "Why do you think people travel abroad more than they used to? "
            "Do you think tourism always benefits local communities?"
        ),
    },
]


async def _upsert_sets(session: AsyncSession) -> int:
    count = 0
    for values in _SETS:
        code = str(values["set_code"])
        current = await session.get(SetModel, code)
        if current is None:
            session.add(SetModel(**values))  # type: ignore[arg-type]
            count += 1
        else:
            for key, value in values.items():
                setattr(current, key, value)
    await session.flush()
    return count


async def _upsert_keys(session: AsyncSession) -> int:
    keys = dict(_KEYS)
    keys["DEMO-GR-M01"] = _mock_keys()

    count = 0
    for set_code, items in keys.items():
        existing = {
            row.q_no: row
            for row in (
                await session.execute(
                    select(AnswerKey).where(AnswerKey.set_code == set_code)
                )
            ).scalars()
        }
        for q_no, answer, accept_also, tag in items:
            current = existing.get(q_no)
            if current is None:
                session.add(
                    AnswerKey(
                        set_code=set_code,
                        q_no=q_no,
                        answer=answer,
                        accept_also=accept_also,
                        tag=tag,
                    )
                )
                count += 1
            else:
                current.answer = answer
                current.accept_also = accept_also
                current.tag = tag
    await session.flush()
    return count


async def _upsert_levels(session: AsyncSession) -> int:
    count = 0
    for scope, bands in _LEVELS.items():
        for row in (
            await session.execute(select(Level).where(Level.scope == scope))
        ).scalars():
            await session.delete(row)
        await session.flush()
        for raw_min, raw_max, level, label in bands:
            session.add(
                Level(
                    scope=scope,
                    raw_min=raw_min,
                    raw_max=raw_max,
                    level=level,
                    label=label,
                )
            )
            count += 1
    await session.flush()
    return count


async def _upsert_ai_tasks(session: AsyncSession) -> int:
    count = 0
    for values in _AI_TASKS:
        code = str(values["code"])
        current = (
            await session.execute(select(AiTask).where(AiTask.code == code))
        ).scalar_one_or_none()
        if current is None:
            session.add(AiTask(**values))  # type: ignore[arg-type]
            count += 1
        else:
            for key, value in values.items():
                setattr(current, key, value)
    await session.flush()
    return count


async def _ensure_student(
    session: AsyncSession, phone: str, full_name: str
) -> tuple[Student, bool]:
    cohort = await repo.get_or_create_cohort(session, DEMO_COHORT)
    student = await repo.get_student_by_phone(session, phone)
    if student is not None:
        student.cohort_id = cohort.id
        await session.flush()
        return student, False

    student = Student(
        full_name=full_name,
        phone=phone,
        cohort_id=cohort.id,
        status=StudentStatus.INVITED,
        note=f"demo · {date.today().isoformat()}",
    )
    session.add(student)
    await session.flush()
    return student, True


async def seed_demo(
    session: AsyncSession,
    *,
    phone: str | None = None,
    full_name: str = "Demo o'quvchi",
) -> str:
    """Demo to'plamlar, kalitlar, darajalar va AI topshiriqlarini yozadi."""
    lines = ["<b>Demo kontent yozildi</b>", ""]
    lines.append(f"To'plamlar: +{await _upsert_sets(session)} (jami {len(_SETS)})")
    lines.append(f"Javob kaliti: +{await _upsert_keys(session)} qator")
    lines.append(f"Daraja shkalasi: {await _upsert_levels(session)} qator")
    lines.append(f"AI topshiriqlari: +{await _upsert_ai_tasks(session)}")

    if phone:
        normalized = normalize_phone(phone)
        if not normalized:
            lines.append(f"\n⚠️ Telefon raqamini o'qib bo'lmadi: {phone}")
        else:
            student, created = await _ensure_student(session, normalized, full_name)
            state = "qo'shildi" if created else "allaqachon bor edi"
            lines.append(f"\nO'quvchi {state}: {student.full_name} · {normalized}")

    lines.append("\nBotda /start → raqamni yuborish → menyu ochiladi.")
    return "\n".join(lines)
