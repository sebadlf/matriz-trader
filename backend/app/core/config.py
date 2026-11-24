"""Configuración tipada del backend, leída del `.env` de la raíz del repositorio."""

import sys
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Final, Literal

from pydantic import (
    Field,
    HttpUrl,
    PostgresDsn,
    SecretStr,
    StringConstraints,
    ValidationError,
    field_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV_FILE: Final = Path(__file__).resolve().parents[3] / ".env"  # <repo>/.env

# Defaults de cada librería (entornos de prueba, no producción).
PRIMARY_BASE_URL_DEFAULT: Final = HttpUrl("https://api.remarkets.primary.com.ar")
MARKET_DATA_BASE_URL_DEFAULT: Final = HttpUrl("https://market-data-develop.bbsa.com.ar/api")

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


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

    # --- matriz-client (nombres exactos que lee la librería) ---
    primary_user: NonEmptyStr
    primary_password: SecretStr
    primary_base_url: HttpUrl = PRIMARY_BASE_URL_DEFAULT

    # --- market-data-client (nombres exactos que lee la librería) ---
    market_data_client_id: NonEmptyStr
    market_data_client_secret: SecretStr
    market_data_audience: NonEmptyStr
    market_data_auth0_token_url: HttpUrl
    market_data_base_url: HttpUrl = MARKET_DATA_BASE_URL_DEFAULT

    @field_validator("primary_password", "market_data_client_secret")
    @classmethod
    def _secret_not_blank(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().strip():
            msg = "no puede estar vacía"
            raise ValueError(msg)
        return value


def _errors(exc: ValidationError) -> list[tuple[str, str]]:
    """`(VARIABLE, mensaje)` por error, sin `input_value` (puede contener secretos)."""
    result: list[tuple[str, str]] = []
    for error in exc.errors(include_input=False, include_url=False):
        loc = error["loc"]
        name = str(loc[0]).upper() if loc else "<desconocida>"
        result.append((name, error["msg"]))
    return result


def _invalid_variables(exc: ValidationError) -> list[str]:
    return list(dict.fromkeys(name for name, _ in _errors(exc)))


def _format_errors(exc: ValidationError) -> str:
    """Una línea por error, `VARIABLE: mensaje`."""
    return "\n".join(f"  - {name}: {msg}" for name, msg in _errors(exc))


def load_settings() -> Settings:
    """Carga y valida la configuración; si es inválida, aborta con exit 1 nombrando la variable."""
    try:
        return Settings()
    except ValidationError as exc:
        names = ", ".join(_invalid_variables(exc))
        sys.stderr.write(f"Configuración inválida: {names}\n{_format_errors(exc)}\n")
        # `from None`: el traceback encadenado repetiría el input (con secretos).
        raise SystemExit(1) from None


@lru_cache
def get_settings() -> Settings:
    """Settings cacheadas para el proceso."""
    return load_settings()
