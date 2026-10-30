"""Adaptador tipado sobre `matriz-client` (AC-17).

Es el único módulo que importa `matriz_client`.
"""

from typing import Protocol

import httpx
from matriz_client import Client, MatrizClientError

from worker.settings import WorkerSettings


class GatewayError(Exception):
    """Fallo al conectar o autenticar contra Matriz."""


class MatrizGateway(Protocol):
    def connect(self) -> None:
        """Conecta y autentica; lanza `GatewayError` si falla."""
        ...

    def close(self) -> None: ...


class MatrizClientGateway:
    def __init__(self, settings: WorkerSettings) -> None:
        # Credenciales siempre explícitas: con `None` la librería cae a `PRIMARY_*` del entorno.
        self._client = Client(
            base_url=settings.matriz_base_url,
            username=settings.matriz_username,
            password=settings.matriz_password.get_secret_value(),
        )

    def connect(self) -> None:
        # `Client` no tiene `connect()`: `login()` valida las credenciales contra la API.
        try:
            self._client.login()
        except (MatrizClientError, httpx.HTTPError) as exc:
            raise GatewayError(str(exc)) from exc

    def close(self) -> None:
        self._client.close()
