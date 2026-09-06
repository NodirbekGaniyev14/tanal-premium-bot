from __future__ import annotations

from enum import StrEnum


class Section(StrEnum):
    """`sets.section` — to'plam qaysi bo'limga tegishli."""

    GRAMMAR_TOPIC = "grammar_topic"
    GRAMMAR_MOCK = "grammar_mock"
    READING = "reading"
    LISTENING = "listening"


#: Daraja shkalasi (`levels.scope`) qaysi bo'limlar uchun qidiriladi.
SCOPE_BY_SECTION: dict[Section, str] = {
    Section.GRAMMAR_TOPIC: "grammar_topic",
    Section.GRAMMAR_MOCK: "grammar_mock",
    Section.READING: "reading",
    Section.LISTENING: "listening",
}


class StudentStatus(StrEnum):
    INVITED = "invited"
    ACTIVE = "active"
    BLOCKED = "blocked"


class FileKind(StrEnum):
    """`file_cache.kind` — qaysi turdagi nusxa keshlangan."""

    PDF = "pdf"
    THEORY = "theory"
    AUDIO = "audio"


class AiKind(StrEnum):
    WRITING = "writing"
    SPEAKING = "speaking"
