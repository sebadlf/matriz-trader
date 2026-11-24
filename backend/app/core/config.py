"""Configuración tipada del backend, leída del `.env` de la raíz del repositorio."""

import sys
from functools import lru_cache
from pathlib import Path
from typing import Final, Literal

from pydantic import Field, PostgresDsn, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV_FILE: Final = Path(__file__).resolve().parents[3] / ".env"  # <repo>/.env


class Settings(BaseSettings):
    """Variables de entorno del backend. El entorno tiene prioridad sobre el `.env`."""

    model_config = SettingsConfigDict(
        env_file=ROOT_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: Literal["development", "production"] = "development"
    database_url: PostgresDsn
    # Todas las interfaces a propósito: en Docker el puerto se publica desde el contenedor.
    backend_host: str = "0.0.0.0"  # noqa: S104
    backend_port: int = Field(default=8000, ge=1, le=65535)
    log_level: Literal["critical", "error", "warning", "info", "debug"] = "info"


def _invalid_variables(exc: ValidationError) -> list[str]:
    names: list[str] = []
    for error in exc.errors():
        loc = error["loc"]
        name = str(loc[0]).upper() if loc else "<desconocida>"
        if name not in names:
            names.append(name)
    return names


def load_settings() -> Settings:
    """Carga y valida la configuración; si es inválida, aborta con exit 1 nombrando la variable."""
    try:
        return Settings()
    except ValidationError as exc:
        names = ", ".join(_invalid_variables(exc))
        sys.stderr.write(f"Configuración inválida: {names}\n{exc}\n")
        raise SystemExit(1) from exc


@lru_cache
def get_settings() -> Settings:
    """Settings cacheadas para el proceso."""
    return load_settings()
