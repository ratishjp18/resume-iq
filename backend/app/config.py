"""Application settings, loaded from environment variables / backend/.env."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
VAR_DIR = BACKEND_DIR / "var"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", env_prefix="RESUMEIQ_", extra="ignore")

    database_url: str = f"sqlite:///{(VAR_DIR / 'resumeiq.db').as_posix()}"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    max_upload_bytes: int = 5 * 1024 * 1024
    max_pdf_pages: int = 50
    max_resume_chars: int = 100_000
    max_job_chars: int = 30_000

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    model_cache_dir: str = str(VAR_DIR / "models")
    preload_model: bool = True
    auto_migrate: bool = True

    # Matching thresholds. NOT calibrated: validate against labeled examples before relying on them.
    threshold_semantic_match: float = 0.55  # statement-only requirement (no catalog skill) -> matched
    threshold_semantic_uncertain: float = 0.40  # statement-only requirement -> uncertain
    threshold_related_skill: float = 0.45  # related same-category skill passage for a missing skill -> uncertain
    threshold_semantic_only_skill: float = 0.50  # purely semantic hint for a skill never mentioned -> uncertain

    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
