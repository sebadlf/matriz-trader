"""Servicio de market data con una fuente fake: paginación, mapeo, filas vacías y errores."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Final

import httpx
import pytest
from market_data_client import (
    AsyncClient,
    BookLevel,
    EntryValue,
    MarketDataAPIError,
    MarketDataAuthError,
    MarketDataEntries,
    MarketDataSnapshot,
)
from structlog.testing import capture_logs

from app.core.config import Settings
from app.domain.errors import MarketDataUnavailableError
from app.services.market_data import (
    MAX_PAGES,
    PAGE_SIZE,
    fetch_all_snapshots,
    list_market_data,
    open_market_data_client,
    snapshot_to_row,
)
from tests.conftest import TEST_CREDENTIALS

NOW: Final = datetime(2026, 11, 24, 14, 3, 11, tzinfo=UTC)
RECEIVED_AT: Final = 1_795_528_991.25  # 2026-11-24T14:03:11.250Z


class FixedClock:
    """Reloj fijo para los tests."""

    def now(self) -> datetime:
        """Siempre `NOW`."""
        return NOW


def make_snapshot(
    symbol: str,
    market_id: str | None = "ROFX",
    market_data: MarketDataEntries | None = None,
    staleness_seconds: float | None = None,
) -> MarketDataSnapshot:
    """Snapshot mínimo; sin `market_data` es un instrumento sin datos."""
    return MarketDataSnapshot(
        symbol=symbol,
        market_id=market_id,
        active=True,
        entries=[],
        market_data=market_data or MarketDataEntries(),
        staleness_seconds=staleness_seconds,
        received_at=RECEIVED_AT,
    )


class FakeSource:
    """Fuente paginada en memoria que registra cada llamada."""

    def __init__(
        self, snapshots: list[MarketDataSnapshot], fail_on_call: int | None = None
    ) -> None:
        self.snapshots = snapshots
        self.fail_on_call = fail_on_call
        self.error: Exception = MarketDataAPIError(503, "upstream down")
        self.calls: list[tuple[bool | None, int | None, int | None]] = []

    async def get_market_data(
        self, *, active: bool | None = None, limit: int | None = None, offset: int | None = None
    ) -> list[MarketDataSnapshot]:
        """Devuelve la página `offset:offset+limit` o lanza `error` en la llamada indicada."""
        self.calls.append((active, limit, offset))
        if self.fail_on_call is not None and len(self.calls) == self.fail_on_call:
            raise self.error
        start = offset or 0
        return self.snapshots[start : start + (limit or len(self.snapshots))]


class EndlessSource:
    """Fuente que ignora `offset` y siempre devuelve una página llena."""

    def __init__(self) -> None:
        self.calls = 0

    async def get_market_data(
        self, *, active: bool | None = None, limit: int | None = None, offset: int | None = None
    ) -> list[MarketDataSnapshot]:
        """Siempre `PAGE_SIZE` snapshots distintos."""
        del active, limit, offset
        self.calls += 1
        return [make_snapshot(f"S{self.calls}-{i}") for i in range(PAGE_SIZE)]


async def test_fetch_all_snapshots_reads_every_page() -> None:
    source = FakeSource([make_snapshot(f"SYM{i:04d}") for i in range(1201)])

    snapshots = await fetch_all_snapshots(source)

    assert len(snapshots) == 1201
    assert source.calls == [(True, PAGE_SIZE, 0), (True, PAGE_SIZE, 500), (True, PAGE_SIZE, 1000)]


async def test_fetch_all_snapshots_exact_multiple_makes_one_extra_empty_call() -> None:
    source = FakeSource([make_snapshot(f"SYM{i:04d}") for i in range(PAGE_SIZE)])

    snapshots = await fetch_all_snapshots(source)

    assert len(snapshots) == PAGE_SIZE
    assert [offset for _, _, offset in source.calls] == [0, PAGE_SIZE]


async def test_fetch_all_snapshots_deduplicates_by_market_and_symbol() -> None:
    first = make_snapshot("AL30", staleness_seconds=1.0)
    last = make_snapshot("AL30", staleness_seconds=2.0)
    other_market = make_snapshot("AL30", market_id="BYMA")

    snapshots = await fetch_all_snapshots(FakeSource([first, other_market, last]))

    assert snapshots == [last, other_market]


async def test_fetch_all_snapshots_caps_pages() -> None:
    source = EndlessSource()

    with capture_logs() as logs, pytest.raises(MarketDataUnavailableError):
        await fetch_all_snapshots(source)

    assert source.calls == MAX_PAGES
    assert logs[0]["event"] == "market_data_fetch_failed"


def test_snapshot_to_row_maps_every_field() -> None:
    snapshot = make_snapshot(
        "GGAL",
        market_data=MarketDataEntries(
            BI=[BookLevel(price=100.0, size=10), BookLevel(price=99.5, size=3)],
            OF=[BookLevel(price=101.0, size=7)],
            LA=EntryValue(price=100.5, size=2, date=1_795_528_990_123),
            OP=98.25,
            HI=102.0,
            LO=97.75,
            CL=EntryValue(price=99.0, date=1_794_900_000_000),
            SE=EntryValue(price=99.1),
            OI=EntryValue(size=12345),
            TV=67890.0,
        ),
        staleness_seconds=2.5,
    )

    row = snapshot_to_row(snapshot)

    assert row.model_dump() == {
        "symbol": "GGAL",
        "market_id": "ROFX",
        "bid_price": Decimal("100.0"),
        "bid_size": Decimal(10),
        "ask_price": Decimal("101.0"),
        "ask_size": Decimal(7),
        "last_price": Decimal("100.5"),
        "last_size": Decimal(2),
        "last_at": datetime(2026, 11, 24, 14, 3, 10, 123000, tzinfo=UTC),
        "open_price": Decimal("98.25"),
        "high_price": Decimal("102.0"),
        "low_price": Decimal("97.75"),
        "close_price": Decimal("99.0"),
        "settlement_price": Decimal("99.1"),
        "open_interest": Decimal(12345),
        "volume": Decimal("67890.0"),
        "spread_pct": Decimal("0.9950"),
        "staleness_seconds": Decimal("2.5"),
        "received_at": datetime(2026, 11, 24, 14, 3, 11, 250000, tzinfo=UTC),
    }


def test_snapshot_to_row_without_data_keeps_symbol_and_nulls() -> None:
    row = snapshot_to_row(make_snapshot("GGAL"))

    dumped = row.model_dump(mode="json")
    assert dumped.pop("symbol") == "GGAL"
    assert dumped.pop("market_id") == "ROFX"
    assert dumped.pop("received_at") == "2026-11-24T14:03:11.250000Z"
    assert set(dumped.values()) == {None}


def test_snapshot_to_row_partial_data_never_fabricates_zero() -> None:
    snapshot = make_snapshot(
        "AL30",
        market_data=MarketDataEntries(
            BI=[BookLevel(price=None, size=None)],
            OF=[BookLevel(price=101.0, size=5)],
            OP=None,
            CL=EntryValue(),
        ),
    )

    row = snapshot_to_row(snapshot)

    assert row.bid_price is None
    assert row.bid_size is None
    assert row.ask_price == Decimal("101.0")
    assert row.spread_pct is None
    assert row.open_price is None
    assert row.close_price is None
    assert "0" not in row.model_dump(mode="json").values()


def test_snapshot_to_row_serializes_decimals_as_strings() -> None:
    snapshot = make_snapshot(
        "AL30",
        market_data=MarketDataEntries(
            BI=[BookLevel(price=0.1, size=1)], OF=[BookLevel(price=0.3, size=1)]
        ),
    )

    dumped = snapshot_to_row(snapshot).model_dump(mode="json")

    assert dumped["bid_price"] == "0.1"
    assert dumped["ask_price"] == "0.3"
    assert dumped["spread_pct"] == "100.0000"


async def test_list_market_data_sorts_rows_and_stamps_fetched_at() -> None:
    source = FakeSource(
        [
            make_snapshot("GGAL", "ROFX"),
            make_snapshot("AL30", "ROFX"),
            make_snapshot("AL30", "BYMA"),
        ]
    )

    response = await list_market_data(source, FixedClock())

    assert [(row.symbol, row.market_id) for row in response.items] == [
        ("AL30", "BYMA"),
        ("AL30", "ROFX"),
        ("GGAL", "ROFX"),
    ]
    assert response.fetched_at == NOW


async def test_list_market_data_empty_catalog() -> None:
    response = await list_market_data(FakeSource([]), FixedClock())

    assert response.items == []


@pytest.mark.parametrize(
    ("error", "status_code"),
    [
        (MarketDataAuthError(401, "unauthorized"), 401),
        (MarketDataAPIError(503, "service unavailable"), 503),
        (httpx.ReadTimeout("timed out"), None),
        (httpx.ConnectError("connection refused"), None),
    ],
)
@pytest.mark.parametrize("fail_on_call", [1, 2])
async def test_list_market_data_upstream_failure_raises_without_partial_data(
    error: Exception, status_code: int | None, fail_on_call: int
) -> None:
    source = FakeSource([make_snapshot(f"SYM{i:04d}") for i in range(700)], fail_on_call)
    source.error = error

    with capture_logs() as logs, pytest.raises(MarketDataUnavailableError) as exc_info:
        await list_market_data(source, FixedClock())

    assert exc_info.value.status == 502
    assert exc_info.value.__cause__ is error
    assert logs == [
        {
            "event": "market_data_fetch_failed",
            "log_level": "warning",
            "error_type": type(error).__name__,
            "status_code": status_code,
        }
    ]
    assert TEST_CREDENTIALS["MARKET_DATA_CLIENT_SECRET"] not in str(logs)


async def test_open_market_data_client_builds_async_client_from_settings() -> None:
    settings = Settings(_env_file=None)

    async with open_market_data_client(settings) as source:
        assert isinstance(source, AsyncClient)
        assert TEST_CREDENTIALS["MARKET_DATA_CLIENT_SECRET"] not in repr(source)
