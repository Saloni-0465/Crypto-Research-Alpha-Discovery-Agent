from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

    app_env: str = "dev"
    app_name: str = "Autonomous Crypto Research & Alpha Discovery Agent"
    api_prefix: str = "/api"

    database_url: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/crypto_agent"
    redis_url: str = "redis://redis:6379/0"

    # Gemini Developer API
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"
    gemini_embeddings_model: str = "gemini-embedding-001"
    gemini_embeddings_dim: int = 1536

    request_timeout_s: float = 20.0

    db_auto_create: bool = True
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    coingecko_base_url: str = "https://api.coingecko.com/api/v3"
    binance_base_url: str = "https://api.binance.com"

    # Background jobs
    celery_broker_url: str = "redis://redis:6379/1"
    celery_result_backend: str = "redis://redis:6379/2"

    # Vector index persistence (mounted volume in docker-compose)
    faiss_dir: str = "data/faiss"


settings = Settings()
