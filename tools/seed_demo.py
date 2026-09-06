"""Demo kontentni bazaga yozadi.

    python -m tools.seed_demo
    python -m tools.seed_demo --phone +998901234567 --name "Nodirbek"

Botning o'zidan ham qilish mumkin: admin sifatida /demo yoki
/demo +998901234567
"""

from __future__ import annotations

import argparse
import asyncio
import re

from app.db.base import get_engine, session_scope
from app.services.demo_seed import seed_demo

_TAGS = re.compile(r"</?b>")


async def _run(phone: str | None, name: str) -> None:
    async with session_scope() as session:
        report = await seed_demo(session, phone=phone, full_name=name)
    print(_TAGS.sub("", report))
    await get_engine().dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Demo kontentni yozish")
    parser.add_argument("--phone", help="sinov o'quvchisining telefon raqami")
    parser.add_argument("--name", default="Demo o'quvchi", help="sinov o'quvchisi ismi")
    args = parser.parse_args()
    asyncio.run(_run(args.phone, args.name))


if __name__ == "__main__":
    main()
