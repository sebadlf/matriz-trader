"""Configuración del worker leída del `.env` único de la raíz (AC-17, AC-18, AC-26)."""

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from model import root_env_file


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=root_env_file(), extra="ignore")

    matriz_base_url: str
    matriz_username: str
    matriz_password: SecretStr
    worker_heartbeat_seconds: float = 30.0
    log_level: str = "INFO"
