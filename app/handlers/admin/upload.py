"""PDF va audio yuklash: fayl bir marta botga yuboriladi, bazada `file_id` qoladi."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app import texts
from app.db import repo
from app.db.models import SetModel
from app.filters import IsAdmin
from app.states import AdminUpload

router = Router(name="admin-upload")
router.message.filter(IsAdmin())


@router.message(Command("upload"))
async def start_upload(message: Message, state: FSMContext) -> None:
    await state.set_state(AdminUpload.waiting_files)
    await message.answer(texts.ADMIN_UPLOAD_WAIT)


@router.message(AdminUpload.waiting_files, Command("done"))
async def finish_upload(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Yuklash rejimi yopildi.")


def _attach(item: SetModel, file_name: str, file_id: str) -> str | None:
    """Fayl nomiga qarab kerakli ustunga `file_id` yozadi."""
    if item.pdf_file == file_name:
        item.pdf_file_id = file_id
        return "test PDF"
    if item.theory_file == file_name:
        item.theory_file_id = file_id
        return "nazariya PDF"
    if item.audio_file == file_name:
        item.audio_file_id = file_id
        return "audio"
    return None


@router.message(AdminUpload.waiting_files, F.document | F.audio | F.voice)
async def receive_file(message: Message, session: AsyncSession) -> None:
    media = message.document or message.audio
    if media is None:
        await message.answer("Faylni hujjat yoki audio sifatida yuboring.")
        return

    file_name = getattr(media, "file_name", None)
    if not file_name:
        await message.answer(
            "Faylning nomi yo'q. Uni hujjat sifatida, nomi bilan yuboring."
        )
        return

    if file_name.lower().endswith(".xlsx"):
        return  # Excel importi alohida handlerda

    targets = await repo.get_set_by_file_name(session, file_name)
    ai_targets = await repo.get_ai_task_by_file_name(session, file_name)
    if not targets and not ai_targets:
        await message.answer(
            f"<code>{file_name}</code> hech qaysi to'plamga bog'lanmagan.\n"
            "sets.xlsx yoki ai_tasks.xlsx dagi nom bilan aynan bir xil bo'lsin."
        )
        return

    attached: list[str] = []
    for item in targets:
        role = _attach(item, file_name, media.file_id)
        if role:
            attached.append(f"{item.set_code} → {role}")
            await repo.drop_cached_files(session, item.set_code)

    for task in ai_targets:
        task.image_file_id = media.file_id
        attached.append(f"{task.code} → topshiriq rasmi")

    await session.flush()
    await message.answer("✅ Biriktirildi:\n" + "\n".join(attached))
