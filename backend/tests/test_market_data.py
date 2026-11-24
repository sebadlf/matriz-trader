"""`GET /api/market-data` con una fuente fake (AC-1, AC-2, AC-20, AC-21)."""

import json
from typing import Any

import httpx
import pytest
from market_data_client import (
    AsyncClient as MarketDataAsyncClient,
)
from market_data_client import (
    BookLevel,
    EntryValue,
    MarketDataAPIError,
    MarketDataAuthError,
    MarketDataEntries,
)

from app.api.deps import get_market_data_source
from app.core.clock import get_clock
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.main import create_app
from app.services.market_data import PAGE_SIZE
from tests.conftest import TEST_CREDENTIALS
from tests.test_market_data_service import NOW, FakeSource, FixedClock, make_snapshot


async def _get(source: FakeSource, path: str = "/api/market-data") -> httpx.Response:
    app = create_app()
    app.dependency_overrides[get_market_data_source] = lambda: source
    app.dependency_overrides[get_clock] = FixedClock
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http_client:
        return await http_client.get(path)


async def test_list_market_data_returns_every_subscribed_instrument() -> None:
    source = FakeSource([make_snapshot(f"SYM{i:04d}") for i in range(1201)])

    response = await _get(source)

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1201
    assert body["fetched_at"] == NOW.isoformat().replace("+00:00", "Z")
    assert source.calls == [(True, PAGE_SIZE, 0), (True, PAGE_SIZE, 500), (True, PAGE_SIZE, 1000)]


async def test_list_market_data_serializes_decimals_as_strings() -> None:
    snapshot = make_snapshot(
        "GGAL",
        market_data=MarketDataEntries(
            BI=[BookLevel(price=100.0, size=10)],
            OF=[BookLevel(price=101.0, size=7)],
            LA=EntryValue(price=100.5, size=2, date=1_795_528_990_123),
            CL=EntryValue(price=99.0),
            TV=67890.0,
        ),
        staleness_seconds=2.5,
    )

    response = await _get(FakeSource([snapshot, make_snapshot("AL30")]))

    assert response.status_code == 200
    first, second = response.json()["items"]
    assert second["symbol"] == "GGAL"
    assert second["bid_price"] == "100.0"
    assert second["ask_size"] == "7"
    assert second["spread_pct"] == "0.9950"
    assert second["last_at"] == "2026-11-24T14:03:10.123000Z"
    assert second["volume"] == "67890.0"
    assert second["staleness_seconds"] == "2.5"
    assert second["open_price"] is None
    assert first["symbol"] == "AL30"
    assert first["bid_price"] is None
    assert first["spread_pct"] is None


@pytest.mark.parametrize(
    "error",
    [
        MarketDataAuthError(401, "unauthorized"),
        MarketDataAPIError(503, "upstream down"),
        httpx.ReadTimeout("timeout"),
        httpx.ConnectError("connection refused"),
    ],
    ids=lambda exc: type(exc).__name__,
)
@pytest.mark.parametrize("fail_on_call", [1, 2])
async def test_list_market_data_failure_is_502_problem(error: Exception, fail_on_call: int) -> None:
    source = FakeSource([make_snapshot(f"SYM{i:04d}") for i in range(PAGE_SIZE + 1)], fail_on_call)
    source.error = error

    response = await _get(source)

    assert response.status_code == 502
    assert response.headers["content-type"] == "application/problem+json"
    body = response.json()
    assert "items" not in body
    assert body["status"] == 502
    assert body["title"] == "Market data no disponible"
    assert body["instance"] == "/api/market-data"
    assert body["correlation_id"] == response.headers["X-Request-ID"]


async def test_list_market_data_failure_logs_correlation_id_without_secrets(
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure_logging("production", "info")
    source = FakeSource([make_snapshot("GGAL")], fail_on_call=1)
    source.error = MarketDataAuthError(
        401, f"bad secret {TEST_CREDENTIALS['MARKET_DATA_CLIENT_SECRET']}"
    )

    response = await _get(source)

    out = capsys.readouterr().out
    events: list[dict[str, Any]] = [
        json.loads(line) for line in out.splitlines() if line.startswith("{")
    ]
    failures = [e for e in events if e["event"] == "market_data_fetch_failed"]
    assert len(failures) == 1
    assert failures[0]["error_type"] == "MarketDataAuthError"
    assert failures[0]["correlation_id"] == response.headers["X-Request-ID"]
    assert TEST_CREDENTIALS["MARKET_DATA_CLIENT_SECRET"] not in out


async def test_list_market_data_is_published_in_openapi() -> None:
    operation = create_app().openapi()["paths"]["/api/market-data"]["get"]

    assert operation["operationId"] == "listMarketData"
    assert operation["tags"] == ["market-data"]
    assert "502" in operation["responses"]


async def test_get_market_data_source_yields_a_real_client() -> None:
    get_settings.cache_clear()
    try:
        sources = get_market_data_source(get_settings())
        source = await anext(sources)
        assert isinstance(source, MarketDataAsyncClient)
        with pytest.raises(StopAsyncIteration):
            await anext(sources)
    finally:
        get_settings.cache_clear()
