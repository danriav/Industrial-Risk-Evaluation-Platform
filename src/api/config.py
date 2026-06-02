from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _parse_csv(value: str | None, default: list[str]) -> list[str]:
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_path(value: str | None, default: str) -> Path:
    path = Path(value or default)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


@dataclass(frozen=True)
class Settings:
    app_name: str = "MERO API"
    database_url: str = os.getenv("DATABASE_URL", "postgresql+psycopg://mero_app:change_me@localhost:5432/mero")
    cors_origins: list[str] = None  # type: ignore[assignment]
    force_https: bool = _parse_bool(os.getenv("FORCE_HTTPS"), False)
    basic_auth_username: str = os.getenv("BASIC_AUTH_USERNAME", "mero_admin")
    basic_auth_password: str = os.getenv("BASIC_AUTH_PASSWORD", "CHANGE_ME_BASIC_AUTH_PASSWORD")
    model_path: Path = _parse_path(os.getenv("MODEL_PATH"), "artifacts/models/random_forest.joblib")

    def __post_init__(self) -> None:
        if self.cors_origins is None:
            object.__setattr__(
                self,
                "cors_origins",
                _parse_csv(os.getenv("CORS_ORIGINS"), ["http://localhost:3000"]),
            )


settings = Settings()
