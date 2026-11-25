"""Tipo de instrumento de Matriz, resuelto con `matriz-client` y cacheado 10 minutos.

Consulta un solo instrumento con `get_instrument_detail(symbol, market_id)`, lo clasifica
con la tabla CFI pura de `app.domain.utils_instrument` y guarda el resultado en memoria.
Las excepciones de `matriz-client` y de red se propagan sin tocar (AC-7).
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Final, Protocol

import structlog
from matriz_client import InstrumentDetail, MarketId

from app.core.clock import Clock, SystemClock
from app.domain.errors import InstrumentNotFoundError, UnclassifiedInstrumentError
from app.domain.utils_instrument import InstrumentType, classify_cficode

logger = structlog.get_logger(__name__)

CACHE_TTL: Final = timedelta(minutes=10)
DEFAULT_MARKET_ID: Final[MarketId] = "ROFX"
"""Mismo default que `matriz-client` (AC-3)."""


class InstrumentDetailSource(Protocol):
    """Lo que el servicio usa de `matriz_client.AsyncClient`; se reemplaza en tests."""

    async def get_instrument_detail(
        self, symbol: str, market_id: MarketId = "ROFX"
    ) -> InstrumentDetail:
        """Detalle de un instrumento por símbolo y mercado."""
        ...


@dataclass(frozen=True, slots=True)
class _CacheEntry:
    instrument_type: InstrumentType
    expires_at: datetime  # UTC, con tzinfo


class InstrumentTypeCache:
    """Caché en memoria por `(market_id, symbol)`; solo guarda resoluciones exitosas."""

    def __init__(self, clock: Clock, ttl: timedelta = CACHE_TTL) -> None:
        self._clock = clock
        self._ttl = ttl
        self._entries: dict[tuple[str, str], _CacheEntry] = {}

    def get(self, symbol: str, market_id: str) -> InstrumentType | None:
        """El tipo cacheado si sigue vigente; `None` si no hay entrada o venció."""
        key = (market_id, symbol)
        entry = self._entries.get(key)
        if entry is None:
            return None
        if self._clock.now() >= entry.expires_at:
            del self._entries[key]
            return None
        return entry.instrument_type

    def put(self, symbol: str, market_id: str, instrument_type: InstrumentType) -> None:
        """Guarda el tipo con vencimiento `now + ttl`."""
        self._entries[(market_id, symbol)] = _CacheEntry(
            instrument_type=instrument_type, expires_at=self._clock.now() + self._ttl
        )

    def clear(self) -> None:
        """Vacía el caché."""
        self._entries.clear()


_default_cache: Final = InstrumentTypeCache(SystemClock())


async def get_instrument_type(
    source: InstrumentDetailSource,
    symbol: str,
    market_id: MarketId = DEFAULT_MARKET_ID,
    *,
    cache: InstrumentTypeCache = _default_cache,
) -> InstrumentType:
    """Tipo del instrumento `symbol` en `market_id` (AC-1 a AC-7).

    - Hit vigente del caché → se devuelve sin consultar a Matriz.
    - Detalle cuyo `instrumentId` no coincide exactamente → `InstrumentNotFoundError` (AC-2, AC-6).
    - CFI `None` o fuera de la tabla → log `warning` y `UnclassifiedInstrumentError` (AC-5).
    - Excepciones de `matriz-client` o de red → se propagan intactas (AC-7).
    """
    cached = cache.get(symbol, market_id)
    if cached is not None:
        return cached

    detail = await source.get_instrument_detail(symbol, market_id)
    if detail.instrumentId.symbol != symbol or detail.instrumentId.marketId != market_id:
        raise InstrumentNotFoundError(
            f"No existe el instrumento {symbol!r} en el mercado {market_id!r}."
        )

    instrument_type = classify_cficode(detail.cficode)
    if instrument_type is None:
        logger.warning(
            "instrument_type_unclassified",
            symbol=symbol,
            market_id=market_id,
            cficode=detail.cficode,
        )
        raise UnclassifiedInstrumentError(
            f"El instrumento {symbol!r} del mercado {market_id!r} tiene un CFI sin clasificar: "
            f"{detail.cficode!r}."
        )

    cache.put(symbol, market_id, instrument_type)
    return instrument_type
