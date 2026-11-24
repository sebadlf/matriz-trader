"""Market data de todos los instrumentos suscriptos, obtenida con `market-data-client`.

Pagina `get_market_data(active=True)` hasta agotar el catálogo, convierte cada snapshot con
las funciones puras de `app.domain.market_data` y traduce cualquier fallo de la librería o
de red a `MarketDataUnavailableError` (502), sin devolver datos parciales.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Final, Protocol

import httpx
import structlog
from market_data_client import AsyncClient, MarketDataError, MarketDataSnapshot

from app.core.clock import Clock
from app.core.config import Settings
from app.domain.errors import MarketDataUnavailableError
from app.domain.market_data import epoch_ms_to_utc, epoch_s_to_utc, spread_pct, to_decimal
from app.schemas.market_data import MarketDataResponse, MarketDataRow

logger = structlog.get_logger(__name__)

PAGE_SIZE: Final = 500
MAX_PAGES: Final = 100
"""Tope defensivo contra un servicio que no corta la paginación."""

UNAVAILABLE_DETAIL: Final = "No se pudo obtener la market data. Reintentá en unos segundos."


class MarketDataSource(Protocol):
    """Lo que el servicio usa de `market_data_client.AsyncClient`; se reemplaza en tests."""

    async def get_market_data(
        self, *, active: bool | None = None, limit: int | None = None, offset: int | None = None
    ) -> list[MarketDataSnapshot]:
        """Una página de snapshots del catálogo de market data."""
        ...


@asynccontextmanager
async def open_market_data_client(settings: Settings) -> AsyncIterator[MarketDataSource]:
    """Cliente nuevo por request, cerrado al salir del bloque `async with`."""
    async with AsyncClient(
        base_url=str(settings.market_data_base_url).rstrip("/"),
        client_id=settings.market_data_client_id,
        client_secret=settings.market_data_client_secret.get_secret_value(),
        audience=settings.market_data_audience,
        auth0_token_url=str(settings.market_data_auth0_token_url),
    ) as client:
        yield client


async def fetch_all_snapshots(source: MarketDataSource) -> list[MarketDataSnapshot]:
    """Todas las páginas de `active=True`; corta con la primera página incompleta (AC-1).

    Si dos páginas traen el mismo `(market_id, symbol)` se conserva el último.
    Más de `MAX_PAGES` páginas → `MarketDataUnavailableError`.
    """
    by_key: dict[tuple[str, str], MarketDataSnapshot] = {}
    for page in range(MAX_PAGES):
        batch = await source.get_market_data(active=True, limit=PAGE_SIZE, offset=page * PAGE_SIZE)
        for snapshot in batch:
            by_key[(snapshot.market_id or "", snapshot.symbol)] = snapshot
        if len(batch) < PAGE_SIZE:
            return list(by_key.values())
    logger.warning("market_data_fetch_failed", error_type="MaxPagesExceeded", status_code=None)
    raise MarketDataUnavailableError(UNAVAILABLE_DETAIL)


def snapshot_to_row(snapshot: MarketDataSnapshot) -> MarketDataRow:
    """Mapea un snapshot a una fila; todo valor ausente queda en `None` (AC-2, AC-5, AC-6)."""
    data = snapshot.market_data
    best_bid = data.BI[0] if data.BI else None
    best_ask = data.OF[0] if data.OF else None
    bid_price = to_decimal(best_bid.price) if best_bid else None
    ask_price = to_decimal(best_ask.price) if best_ask else None
    return MarketDataRow(
        symbol=snapshot.symbol,
        market_id=snapshot.market_id,
        bid_price=bid_price,
        bid_size=to_decimal(best_bid.size) if best_bid else None,
        ask_price=ask_price,
        ask_size=to_decimal(best_ask.size) if best_ask else None,
        last_price=to_decimal(data.LA.price),
        last_size=to_decimal(data.LA.size),
        last_at=epoch_ms_to_utc(data.LA.date),
        open_price=to_decimal(data.OP),
        high_price=to_decimal(data.HI),
        low_price=to_decimal(data.LO),
        close_price=to_decimal(data.CL.price),
        settlement_price=to_decimal(data.SE.price),
        open_interest=to_decimal(data.OI.size),
        volume=to_decimal(data.TV),
        spread_pct=spread_pct(bid_price, ask_price),
        staleness_seconds=to_decimal(snapshot.staleness_seconds),
        received_at=epoch_s_to_utc(snapshot.received_at),
    )


async def list_market_data(source: MarketDataSource, clock: Clock) -> MarketDataResponse:
    """Market data de todos los instrumentos suscriptos, ordenada por `symbol` y `market_id`.

    Un error de la librería (`MarketDataError`: auth, 5xx, rate limit, decode) o de red
    (`httpx.HTTPError`) se loguea sin el mensaje (puede incluir URLs o cuerpos) y se relanza
    como `MarketDataUnavailableError` (AC-20, AC-21).
    """
    try:
        snapshots = await fetch_all_snapshots(source)
    except (MarketDataError, httpx.HTTPError) as exc:
        logger.warning(
            "market_data_fetch_failed",
            error_type=type(exc).__name__,
            status_code=getattr(exc, "status_code", None),
        )
        raise MarketDataUnavailableError(UNAVAILABLE_DETAIL) from exc
    rows = sorted(
        (snapshot_to_row(snapshot) for snapshot in snapshots),
        key=lambda row: (row.symbol, row.market_id or ""),
    )
    return MarketDataResponse(items=rows, fetched_at=clock.now())
