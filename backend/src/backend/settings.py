"""Configuración del backend leída del `.env` único de la raíz (AC-13, AC-46, EB-38)."""

import logging

from broker.matriz_gateway import MatrizCredentials
from pydantic import SecretStr, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from model import missing_env_vars, root_env_file

logger = logging.getLogger(__name__)

DEFAULT_MATRIZ_BASE_URL = "https://api.remarkets.primary.com.ar"


class BackendSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=root_env_file(), extra="ignore")

    database_url: str
    cors_origins: str = ""
    log_level: str = "INFO"
    # `MATRIZ_*` son opcionales en el backend: sin ellas `/health` y `export_openapi`
    # siguen funcionando (UB-4) y los endpoints de órdenes responden 503.
    matriz_base_url: str = DEFAULT_MATRIZ_BASE_URL
    matriz_username: str | None = None
    matriz_password: SecretStr | None = None
    # Lista separada por comas: `MATRIZ_ACCOUNTS=REM1234,REM5678`.
    matriz_accounts: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def matriz_account_list(self) -> list[str]:
        """Cuentas sin espacios ni vacíos, deduplicadas preservando el orden."""
        accounts = (account.strip() for account in self.matriz_accounts.split(","))
        return list(dict.fromkeys(account for account in accounts if account))

    @property
    def matriz_credentials(self) -> MatrizCredentials | None:
        """`None` si falta (o está vacío) `MATRIZ_USERNAME` o `MATRIZ_PASSWORD`."""
        username = (self.matriz_username or "").strip()
        password = self.matriz_password.get_secret_value() if self.matriz_password else ""
        if not username or not password:
            return None
        return MatrizCredentials(
            base_url=self.matriz_base_url, username=username, password=password
        )


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
