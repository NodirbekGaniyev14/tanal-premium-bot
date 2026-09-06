from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    waiting_contact = State()


class Solving(StatesGroup):
    """Javob yig'ish holati. `data`: set_code, total_q, raw_chunks, answers."""

    collecting = State()
    confirming = State()


class Writing(StatesGroup):
    """`data`: task_id, task_prompt, task_type, pages (file_id ro'yxati)."""

    choosing_task = State()
    own_task = State()
    collecting_pages = State()


class Speaking(StatesGroup):
    """`data`: task_id, question, part, prep_until."""

    waiting_voice = State()


class AdminImport(StatesGroup):
    waiting_file = State()


class AdminUpload(StatesGroup):
    waiting_files = State()


class Broadcast(StatesGroup):
    waiting_text = State()
    confirming = State()
