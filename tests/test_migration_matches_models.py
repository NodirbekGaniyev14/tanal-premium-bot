"""Migratsiya modellardan orqada qolib ketmasin.

To'liq tekshiruv emas (buning uchun jonli Postgres kerak), lekin yangi ustun
qo'shib migratsiyani unutish — eng ko'p uchraydigan xato, shuni ushlaydi.
"""

from __future__ import annotations

from pathlib import Path

from app.db import models  # noqa: F401  (jadvallar ro'yxatga tushsin)
from app.db.base import Base

MIGRATION = Path("migrations/versions/0001_init.py").read_text(encoding="utf-8")


def test_all_tables_present() -> None:
    missing = [
        name for name in Base.metadata.tables if f'"{name}"' not in MIGRATION
    ]
    assert not missing, f"migratsiyada yo'q jadvallar: {missing}"


def test_all_columns_present() -> None:
    missing: list[str] = []
    for table_name, table in Base.metadata.tables.items():
        for column in table.columns:
            if f'"{column.name}"' not in MIGRATION:
                missing.append(f"{table_name}.{column.name}")
    assert not missing, f"migratsiyada yo'q ustunlar: {missing}"
