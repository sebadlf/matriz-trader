"""Configuración del backend leída del `.env` único de la raíz (AC-13, AC-46)."""

import logging

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from model import missing_env_vars, root_env_file

logger = logging.getLogger(__name__)


class BackendSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=root_env_file(), extra="ignore")

    database_url: str
    cors_origins: str = ""
    log_level: str = "INFO"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


def load_settings() -> BackendSettings:
    """Carga la configuración o termina el proceso con exit code 2 si falta alguna variable."""
    try:
        return BackendSettings()  # pyright: ignore[reportCallIssue]
    except ValidationError as exc:
        missing = missing_env_vars(exc)
        if not missing:
            raise
        logger.error("Missing required environment variables: %s", ", ".join(missing))
        raise SystemExit(2) from exc
