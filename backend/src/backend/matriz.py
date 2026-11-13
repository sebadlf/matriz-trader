"""Provider de Matriz por proceso, caché de instrumentos y traducción de errores (EB-35).

No importa `matriz_client`: todo pasa por `broker.matriz_gateway` (EB-37).
"""

import threading
import time
from collections.abc import Callable

from broker.matriz_gateway import GatewayError, InstrumentRef, MatrizClientGateway, MatrizTrading
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

from backend.settings import BackendSettings

INSTRUMENTS_TTL_SECONDS = 3600.0
NOT_CONFIGURED_DETAIL = "Matriz no está configurado (MATRIZ_USERNAME/MATRIZ_PASSWORD)"


class InstrumentCache:
    """Catálogo de instrumentos en memoria del proceso con TTL; no cachea fallos."""

    def __init__(
        self,
        trading: MatrizTrading,
        ttl_seconds: float = INSTRUMENTS_TTL_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._trading = trading
        self._ttl_seconds = ttl_seconds
        self._clock = clock
        self._lock = threading.Lock()
        self._instruments: list[InstrumentRef] | None = None
        self._fetched_at = 0.0

    def get(self) -> list[InstrumentRef]:
        with self._lock:
            now = self._clock()
            if self._instruments is None or now - self._fetched_at >= self._ttl_seconds:
                # Si falla, propaga `GatewayError` y deja el caché como estaba.
                self._instruments = self._trading.list_instruments()
                self._fetched_at = now
            return list(self._instruments)


def build_trading(settings: BackendSettings) -> MatrizTrading | None:
    """Una instancia por proceso; no hace login (diferido al primer uso)."""
    credentials = settings.matriz_credentials
    return MatrizClientGateway(credentials) if credentials is not None else None


async def _gateway_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    # `GatewayError` ya trae el mensaje sin secretos (redactado en el broker).
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY, content={"detail": f"Matriz: {exc}"}
    )


def install_matriz(
    app: FastAPI, settings: BackendSettings, trading: MatrizTrading | None = None
) -> None:
    """Guarda el provider, el caché y las cuentas en `app.state` y traduce `GatewayError` a 502."""
    resolved = trading if trading is not None else build_trading(settings)
    app.state.trading = resolved
    app.state.instrument_cache = InstrumentCache(resolved) if resolved is not None else None
    app.state.matriz_accounts = settings.matriz_account_list
    app.add_exception_handler(GatewayError, _gateway_error_handler)


def get_trading(request: Request) -> MatrizTrading:
    trading: MatrizTrading | None = getattr(request.app.state, "trading", None)
    if trading is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, NOT_CONFIGURED_DETAIL)
    return trading


def get_instrument_cache(request: Request) -> InstrumentCache:
    cache: InstrumentCache | None = getattr(request.app.state, "instrument_cache", None)
    if cache is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, NOT_CONFIGURED_DETAIL)
    return cache


def get_accounts(request: Request) -> list[str]:
    accounts: list[str] = getattr(request.app.state, "matriz_accounts", [])
    return accounts


def require_configured_account(account_id: str, accounts: list[str]) -> None:
    """422 si la cuenta no está en `MATRIZ_ACCOUNTS`."""
    if account_id not in accounts:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, f"Cuenta no configurada: {account_id}"
        )
