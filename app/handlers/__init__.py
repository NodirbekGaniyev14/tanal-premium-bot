from aiogram import Router

from app.handlers import answers, fallback, menu, sets, speaking, start, writing
from app.handlers.admin import imports as admin_imports
from app.handlers.admin import stats as admin_stats
from app.handlers.admin import upload as admin_upload


def build_router() -> Router:
    """Tartib muhim: admin → kirish → javob dvigateli → AI → menyu → fallback."""
    router = Router(name="root")
    router.include_router(admin_imports.router)
    router.include_router(admin_upload.router)
    router.include_router(admin_stats.router)
    router.include_router(start.router)
    router.include_router(answers.router)
    router.include_router(writing.router)
    router.include_router(speaking.router)
    router.include_router(sets.router)
    router.include_router(menu.router)
    router.include_router(fallback.router)
    return router
