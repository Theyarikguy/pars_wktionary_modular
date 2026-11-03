from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / ".env",  # абсолютный путь к .env в корне проекта
        extra="ignore"
    )

    DATABASE_URL: str = "sqlite:///./app.db"

    API_SERVICE_PORT: int = 8000

    # Настройки пула для SQLite не актуальны (SQLite не поддерживает pool_size и т.п.
    # для файловой БД в async-режиме). Оставляем как опциональные, чтобы не ломать код,
    # который может их читать, но со значениями-заглушками.
    DB_ENGINE_POOL_PRE_PING: bool = False
    DB_ENGINE_POOL_RECYCLE: int = -1
    DB_ENGINE_POOL_SIZE: int = 5
    DB_ENGINE_MAX_OVERFLOW: int = 10
    DB_ENGINE_POOL_TIMEOUT: int = 30

    SECRET_KEY: str = "GLpxkvV5puJp8F9zvJWnOf0SFCm9cWP8xLuvlDSfF1w"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30


settings = Settings()