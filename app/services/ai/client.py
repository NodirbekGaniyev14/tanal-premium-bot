"""Gemini mijozi va demo rejimi.

`GEMINI_API_KEY` bo'sh bo'lsa (yoki `AI_DEMO=true`) bot **demo mijoz** bilan
ishlaydi: writing va speaking oqimi to'liq ishlaydi, natija namunaviy bo'ladi.
Shu tufayli kontent va API kaliti yo'q holatda ham hamma narsani sinash mumkin.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import lru_cache
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.config import get_settings
from app.services.ai.schemas import (
    GrammarError,
    SpeakingReview,
    SpeakingScores,
    WritingError,
    WritingReview,
    WritingScores,
)

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

DEMO_MODEL_NAME = "demo"


class AiError(RuntimeError):
    """Model javob bermadi yoki javobini o'qib bo'lmadi."""


@dataclass(slots=True, frozen=True)
class MediaPart:
    data: bytes
    mime_type: str


@dataclass(slots=True)
class AiResult:
    data: BaseModel
    model: str
    tokens_in: int | None = None
    tokens_out: int | None = None
    demo: bool = False


def parse_json[T: BaseModel](raw: str, schema: type[T]) -> T:
    """Model qaytargan matndan JSON ajratib, sxema bo'yicha tekshiradi."""
    text = (raw or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.split("\n", 1)[1] if "\n" in text else text
        text = text.rsplit("```", 1)[0]
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise AiError("Javobda JSON topilmadi")
    try:
        return schema.model_validate(json.loads(text[start : end + 1]))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise AiError(f"Javob sxemaga mos emas: {exc}") from exc


class AiClient(ABC):
    model_name: str

    @abstractmethod
    async def generate(
        self, *, prompt: str, parts: list[MediaPart], schema: type[T]
    ) -> AiResult: ...


class GeminiClient(AiClient):
    def __init__(self, api_key: str, model: str) -> None:
        self.model_name = model
        self._api_key = api_key
        self._client = None

    def _ensure_client(self):  # noqa: ANN202 — SDK turi importdan keyin ma'lum
        if self._client is None:
            from google import genai  # kech import: paket yo'q bo'lsa ham bot ko'tariladi

            self._client = genai.Client(api_key=self._api_key)
        return self._client

    async def generate(
        self, *, prompt: str, parts: list[MediaPart], schema: type[T]
    ) -> AiResult:
        from google.genai import types

        client = self._ensure_client()
        contents: list[object] = [
            types.Part.from_bytes(data=part.data, mime_type=part.mime_type)
            for part in parts
        ]
        contents.append(prompt)

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
            temperature=0.2,
        )
        try:
            response = await client.aio.models.generate_content(
                model=self.model_name, contents=contents, config=config
            )
        except Exception as exc:  # SDK o'z xatolar iyerarxiyasiga ega
            raise AiError(str(exc)) from exc

        usage = getattr(response, "usage_metadata", None)
        return AiResult(
            data=parse_json(response.text or "", schema),
            model=self.model_name,
            tokens_in=getattr(usage, "prompt_token_count", None),
            tokens_out=getattr(usage, "candidates_token_count", None),
        )


class DemoClient(AiClient):
    """Gemini chaqirmaydi — oqimni sinash uchun namunaviy natija qaytaradi."""

    model_name = DEMO_MODEL_NAME

    async def generate(
        self, *, prompt: str, parts: list[MediaPart], schema: type[T]
    ) -> AiResult:
        if schema is WritingReview:
            data: BaseModel = _demo_writing(len(parts))
        elif schema is SpeakingReview:
            data = _demo_speaking()
        else:  # pragma: no cover — boshqa sxema hozircha yo'q
            raise AiError(f"Demo rejimi bu sxemani bilmaydi: {schema.__name__}")
        return AiResult(data=data, model=DEMO_MODEL_NAME, demo=True)


def _demo_writing(pages: int) -> WritingReview:
    return WritingReview(
        unreadable=False,
        word_count=248,
        transcript=(
            "[DEMO] Bu namunaviy transkript. Haqiqiy rejimda bu yerda "
            f"yuborilgan {pages} ta varaqdan tiklangan insho matni turadi."
        ),
        scores=WritingScores(ta=6.0, cc=6.0, lr=5.5, gra=6.0, overall=6.0),
        errors=[
            WritingError(
                no=1,
                original="I am agree",
                correction="I agree",
                why="agree — fe'l, oldiga «am» qo'yilmaydi",
            ),
            WritingError(
                no=2,
                original="peoples",
                correction="people",
                why="people allaqachon ko'plikda",
            ),
            WritingError(
                no=3,
                original="In nowadays",
                correction="Nowadays",
                why="nowadays oldidan predlog kerak emas",
            ),
        ],
        error_count_total=12,
        strength="Fikr aniq, paragraflar mantiqiy ketma-ketlikda.",
        fix_first="Grammatik aniqlik: artikllar va fe'l shakllari.",
        corrected_text=(
            "[DEMO] Tuzatilgan to'liq matn shu yerda bo'ladi. "
            "Haqiqiy rejimda Gemini inshoni to'liq qayta yozib beradi."
        ),
    )


def _demo_speaking() -> SpeakingReview:
    return SpeakingReview(
        insufficient=False,
        transcript=(
            "[DEMO] Bu namunaviy transkript. Haqiqiy rejimda bu yerda "
            "ovozli javobingizning so'zma-so'z yozuvi turadi."
        ),
        duration_sec=62,
        wpm=118,
        long_pauses=4,
        scores=SpeakingScores(fc=6.5, lr=6.0, gra=6.5, pron=7.0, overall=6.5),
        grammar_errors=[
            GrammarError(quote="I have went there", correction="I have been there"),
            GrammarError(quote="more better", correction="better"),
        ],
        advice=[
            "Javobni «Firstly… Secondly… Finally…» bilan tuzilmaga soling.",
            "Har fikrga bitta aniq misol qo'shing — bu Fluency ni ko'taradi.",
            "«very good» o'rniga «remarkable», «impressive» kabi so'zlarni ishlating.",
        ],
        model_answer=(
            "[DEMO] 7.5 darajali namuna javob shu yerda bo'ladi."
        ),
    )


@lru_cache
def get_client() -> AiClient:
    settings = get_settings()
    if settings.ai_demo_mode:
        logger.warning("AI DEMO rejimi: Gemini chaqirilmaydi, natija namunaviy")
        return DemoClient()
    return GeminiClient(settings.gemini_api_key, settings.gemini_model)
