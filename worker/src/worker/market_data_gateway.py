"""Adaptador tipado sobre `market-data-client` (única fuente de market data).

Es el único módulo del repo que importa `market_data_client`. Nunca obtener
market data con `matriz-client`.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Protocol

import httpx
from market_data_client import Client, MarketDataError

from worker.settings import WorkerSettings


class MarketDataGatewayError(Exception):
    """Fallo al conectar u obtener market data con market-data-client."""


@dataclass(frozen=True, slots=True)
class Quote:
    symbol: str
    last_price: Decimal | None  # None si el feed no entregó LA para el símbolo
    received_at: datetime  # tz-aware UTC (estampado por el cliente)


class MarketDataGateway(Protocol):
    def connect(self) -> None:
        """Verifica conectividad con la API; lanza `MarketDataGatewayError` si falla."""
        ...

    def get_quote(self, symbol: str) -> Quote | None:
        """Último snapshot del símbolo, o None si la API no devuelve filas."""
        ...

    def close(self) -> None: ...


class MarketDataClientGateway:
    def __init__(
        self,
        settings: WorkerSettings,
        *,
        http_client: httpx.Client | None = None,
        max_retries: int = 2,
    ) -> None:
        # Todo explícito: con `None` la librería cae a `MARKET_DATA_*` de os.environ.
        self._client = Client(
            base_url=settings.market_data_base_url,
            client_id=settings.market_data_client_id,
            client_secret=settings.market_data_client_secret.get_secret_value(),
            audience=settings.market_data_audience,
            auth0_token_url=settings.market_data_auth0_token_url,
            http_client=http_client,
            max_retries=max_retries,
        )

    def connect(self) -> None:
        # `get_health()` es anónimo: valida conectividad y URL, no credenciales Auth0.
        try:
            self._client.get_health()
        except (MarketDataError, httpx.HTTPError) as exc:
            raise MarketDataGatewayError(str(exc)) from exc

    def get_quote(self, symbol: str) -> Quote | None:
        try:
            snapshots = self._client.get_latest(symbol=symbol)
        except (MarketDataError, httpx.HTTPError) as exc:
            raise MarketDataGatewayError(str(exc)) from exc
        if not snapshots:
            return None
        snap = snapshots[0]
        price = snap.market_data.LA.price
        return Quote(
            symbol=snap.symbol,
            last_price=None if price is None else Decimal(str(price)),
            received_at=datetime.fromtimestamp(snap.received_at, tz=UTC),
        )

    def close(self) -> None:
        self._client.close()
