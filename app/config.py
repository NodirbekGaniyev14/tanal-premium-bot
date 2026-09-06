from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Telegram
    bot_token: str = Field(alias="BOT_TOKEN")
    admin_chat_id: int = Field(alias="ADMIN_CHAT_ID")
    admin_ids: list[int] = Field(default_factory=list, alias="ADMIN_IDS")

    # Postgres
    postgres_user: str = Field(default="tanal", alias="POSTGRES_USER")
    postgres_password: str = Field(default="tanal", alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="tanal", alias="POSTGRES_DB")
    postgres_host: str = Field(default="postgres", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")

    # Redis
    redis_host: str = Field(default="redis", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")

    # Gemini
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")
    ai_demo: bool = Field(default=False, alias="AI_DEMO")
    ai_daily_limit: int = Field(default=6, alias="AI_DAILY_LIMIT")
    speaking_min_sec: int = Field(default=15, alias="SPEAKING_MIN_SEC")
    speaking_max_sec: int = Field(default=180, alias="SPEAKING_MAX_SEC")
    writing_max_pages: int = Field(default=6, alias="WRITING_MAX_PAGES")

    # Umumiy
    tz: str = Field(default="Asia/Tashkent", alias="TZ")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    content_dir: str = Field(default="/app/content", alias="CONTENT_DIR")

    @field_validator("admin_ids", mode="before")
    @classmethod
    def _split_admin_ids(cls, v: object) -> object:
        if isinstance(v, str):
            return [int(x) for x in v.replace(" ", "").split(",") if x]
        return v

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def ai_demo_mode(self) -> bool:
        """Kalit yo'q bo'lsa yoki majburlansa — Gemini chaqirilmaydi."""
        return self.ai_demo or not self.gemini_api_key.strip()


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
