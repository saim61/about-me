"""Application settings, loaded from environment variables and an optional .env file."""

from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """All configuration lives here. Env vars use the ABOUT_RAG_ prefix."""

    model_config = SettingsConfigDict(
        env_prefix="ABOUT_RAG_",
        env_file=PROJECT_ROOT / ".env",
        extra="ignore",
    )

    knowledge_base_path: Path = PROJECT_ROOT / "data" / "about_saeem.md"
    raw_data_dir: Path = PROJECT_ROOT / "data" / "raw"
    processed_data_dir: Path = PROJECT_ROOT / "data" / "processed"
    system_prompt_path: Path = PROJECT_ROOT / "prompts" / "system_prompt.md"
    log_level: str = "INFO"

    embedding_model: str = "BAAI/bge-small-en-v1.5"
    model_cache_dir: Path = PROJECT_ROOT / ".cache" / "models"
    top_k: int = 3

    # Matches docker-compose.yml. Production overrides it with ABOUT_RAG_DATABASE_URL.
    database_url: SecretStr = SecretStr("postgresql://about_rag:about_rag@localhost:5433/about_rag")

    llm_api_key: SecretStr | None = None


@lru_cache
def get_settings() -> Settings:
    """Return a single shared Settings instance (created on first call)."""
    return Settings()
