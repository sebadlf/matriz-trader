"""`get_instrument_type` con una fuente fake y un reloj controlable: resolución, errores y caché."""

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Final, cast

import httpx
import pytest
from matriz_client import InstrumentDetail, InstrumentId, MarketId, PrimaryAPIError
from structlog.testing import capture_logs

if TYPE_CHECKING:
    from matriz_client.types import CFICode

from app.domain.errors import DomainError, InstrumentNotFoundError, UnclassifiedInstrumentError
from app.domain.utils_instrument import CFI_TO_INSTRUMENT_TYPE, InstrumentType
from app.services.utils_instrument import (
    CACHE_TTL,
    DEFAULT_MARKET_ID,
    InstrumentTypeCache,
    get_instrument_type,
)

NOW: Final = datetime(2026, 11, 25, 14, 0, 0, tzinfo=UTC)
SYMBOL: Final = "AL30 - 48hs"


class MutableClock:
    """Reloj fijo que el test puede adelantar."""

    def __init__(self, now: datetime = NOW) -> None:
        self.current = now

    def now(self) -> datetime:
        """La hora fijada por el test."""
        return self.current


def make_detail(
    cficode: str | None, symbol: str | None = SYMBOL, market_id: MarketId | None = "ROFX"
) -> InstrumentDetail:
    """Detalle mínimo. `cast`: `DYXTXR` y los CFI fuera de tabla no están en `CFICode`."""
    return InstrumentDetail(
        instrumentId=InstrumentId(marketId=market_id, symbol=symbol),
        cficode=cast("CFICode | None", cficode),
    )


class FakeSource:
    """Fuente fake: registra las consultas y devuelve un detalle o lanza una excepción."""

    def __init__(self, result: InstrumentDetail | Exception) -> None:
        self.result = result
        self.calls: list[tuple[str, str]] = []

    async def get_instrument_detail(
        self, symbol: str, market_id: MarketId = "ROFX"
    ) -> InstrumentDetail:
        """Registra `(symbol, market_id)` y devuelve `result`."""
        self.calls.append((symbol, market_id))
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def make_cache() -> InstrumentTypeCache:
    """Caché propio por test, nunca el default del módulo."""
    return InstrumentTypeCache(MutableClock())


@pytest.mark.parametrize(("cficode", "expected"), sorted(CFI_TO_INSTRUMENT_TYPE.items()))
async def test_resolves_each_cfi_in_table(cficode: str, expected: InstrumentType) -> None:
    """AC-1, AC-4: cada CFI de la tabla da su miembro del enum, nunca un `str` crudo."""
    result = await get_instrument_type(
        FakeSource(make_detail(cficode)), SYMBOL, "ROFX", cache=make_cache()
    )
    assert result is expected
    assert type(result) is InstrumentType


async def test_queries_source_with_symbol_and_market() -> None:
    """AC-2: consulta un solo instrumento con el símbolo y el mercado pedidos."""
    source = FakeSource(make_detail("DBXXFR"))
    result = await get_instrument_type(source, SYMBOL, "ROFX", cache=make_cache())
    assert result is InstrumentType.OBLIGACION_NEGOCIABLE
    assert source.calls == [(SYMBOL, "ROFX")]


async def test_uses_rofx_by_default() -> None:
    """AC-3: sin `market_id` se usa `ROFX`, el default de `matriz-client`."""
    source = FakeSource(make_detail("ESXXXX"))
    await get_instrument_type(source, SYMBOL, cache=make_cache())
    assert DEFAULT_MARKET_ID == "ROFX"
    assert source.calls == [(SYMBOL, "ROFX")]


@pytest.mark.parametrize(
    "detail",
    [
        InstrumentDetail(),
        make_detail("ESXXXX", symbol="GGAL - 48hs"),
        make_detail("ESXXXX", symbol=SYMBOL.lower()),
        make_detail("ESXXXX", market_id=None),
    ],
    ids=["empty", "other-symbol", "case-differs", "no-market"],
)
async def test_mismatched_detail_raises_not_found(detail: InstrumentDetail) -> None:
    """AC-2, AC-6: un detalle vacío o de otro instrumento lanza `InstrumentNotFoundError`."""
    cache = make_cache()
    with pytest.raises(InstrumentNotFoundError) as exc_info:
        await get_instrument_type(FakeSource(detail), SYMBOL, "ROFX", cache=cache)
    assert isinstance(exc_info.value, DomainError)
    assert repr(SYMBOL) in exc_info.value.detail
    assert "'ROFX'" in exc_info.value.detail
    assert cache.get(SYMBOL, "ROFX") is None


@pytest.mark.parametrize("cficode", [None, "LRXXXX"])
async def test_unclassified_cfi_raises_and_logs(cficode: str | None) -> None:
    """AC-5: CFI `None` o fuera de la tabla → `warning` estructurado y error tipado."""
    cache = make_cache()
    with capture_logs() as logs, pytest.raises(UnclassifiedInstrumentError) as exc_info:
        await get_instrument_type(FakeSource(make_detail(cficode)), SYMBOL, "ROFX", cache=cache)
    detail = exc_info.value.detail
    assert repr(SYMBOL) in detail
    assert "'ROFX'" in detail
    assert repr(cficode) in detail
    assert logs == [
        {
            "event": "instrument_type_unclassified",
            "log_level": "warning",
            "symbol": SYMBOL,
            "market_id": "ROFX",
            "cficode": cficode,
        }
    ]
    assert cache.get(SYMBOL, "ROFX") is None


@pytest.mark.parametrize(
    "error",
    [PrimaryAPIError("ERROR", "not found"), httpx.ConnectError("boom")],
    ids=["primary-api-error", "network-error"],
)
async def test_propagates_source_exceptions(error: Exception) -> None:
    """AC-7: las excepciones de `matriz-client` y de red se propagan intactas, sin cachear."""
    source = FakeSource(error)
    cache = make_cache()
    with pytest.raises(type(error)) as exc_info:
        await get_instrument_type(source, SYMBOL, "ROFX", cache=cache)
    assert exc_info.value is error
    assert cache.get(SYMBOL, "ROFX") is None


async def test_caches_for_ten_minutes() -> None:
    """Caché: dentro de 10 minutos no consulta de nuevo; al vencer, sí."""
    clock = MutableClock()
    cache = InstrumentTypeCache(clock)
    source = FakeSource(make_detail("DBXXXX"))

    assert await get_instrument_type(source, SYMBOL, cache=cache) is InstrumentType.BONO
    clock.current = NOW + CACHE_TTL - timedelta(microseconds=1)
    assert await get_instrument_type(source, SYMBOL, cache=cache) is InstrumentType.BONO
    assert len(source.calls) == 1

    clock.current = NOW + CACHE_TTL
    assert await get_instrument_type(source, SYMBOL, cache=cache) is InstrumentType.BONO
    assert len(source.calls) == 2
    assert timedelta(minutes=10) == CACHE_TTL


async def test_cache_key_includes_symbol() -> None:
    """Caché: cada símbolo tiene su propia entrada."""
    cache = make_cache()
    cache.put("GGAL - 48hs", "ROFX", InstrumentType.ACCION)
    source = FakeSource(make_detail("DBXXXX"))
    assert await get_instrument_type(source, SYMBOL, cache=cache) is InstrumentType.BONO
    assert source.calls == [(SYMBOL, "ROFX")]


def test_cache_clear() -> None:
    """`clear()` vacía el caché."""
    cache = make_cache()
    cache.put(SYMBOL, "ROFX", InstrumentType.LETRA)
    assert cache.get(SYMBOL, "ROFX") is InstrumentType.LETRA
    cache.clear()
    assert cache.get(SYMBOL, "ROFX") is None
