"""Configuración del worker leída del `.env` único de la raíz (AC-17, AC-18, AC-26)."""

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from model import root_env_file

DEFAULT_MARKET_DATA_BASE_URL = "https://market-data-develop.bbsa.com.ar/api"


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=root_env_file(), extra="ignore")

    matriz_base_url: str
    matriz_username: str
    matriz_password: SecretStr
    market_data_client_id: str
    market_data_client_secret: SecretStr
    market_data_audience: str
    market_data_auth0_token_url: str
    market_data_base_url: str = DEFAULT_MARKET_DATA_BASE_URL
    worker_heartbeat_seconds: float = 30.0
    log_level: str = "INFO"
