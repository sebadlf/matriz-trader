"""Configuración compartida leída del `.env` único de la raíz (AC-26)."""

from pathlib import Path

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


def root_env_file() -> Path | None:
    """Primer `.env` encontrado subiendo desde este archivo; None dentro de Docker."""
    for directory in Path(__file__).resolve().parents:
        candidate = directory / ".env"
        if candidate.is_file():
            return candidate
    return None


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=root_env_file(), extra="ignore")

    database_url: str


def missing_env_vars(exc: ValidationError) -> list[str]:
    """Nombres de env en MAYÚSCULAS de los errores `type == "missing"`, ordenados."""
    return sorted(
        {
            str(error["loc"][0]).upper()
            for error in exc.errors()
            if error["type"] == "missing" and error["loc"]
        }
    )
