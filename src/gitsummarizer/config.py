from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    telegram_bot_token: str = Field(alias="TELEGRAM_BOT_TOKEN")
    gitlab_url: str = Field(default="https://gitlab.com", alias="GITLAB_URL")
    gitlab_token: str = Field(alias="GITLAB_TOKEN")
    gitlab_default_project: Optional[str] = Field(default=None, alias="GITLAB_DEFAULT_PROJECT")
    openai_api_key: str = Field(alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    output_dir: Path = Field(default=Path("./output"), alias="OUTPUT_DIR")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
