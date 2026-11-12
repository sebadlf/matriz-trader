"""Tests del loop, señales y gateways del worker sin red (AC-13, AC-14, AC-15, AC-17, AC-36)."""

import asyncio
import logging
import os
import signal
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import SecretStr
from worker.market_data_gateway import MarketDataGatewayError, Quote
from worker.matriz_gateway import GatewayError, MatrizClientGateway
from worker.runner import run, serve
from worker.settings import WorkerSettings

HEARTBEAT = 0.01
MARKET_DATA_BASE_URL = "https://market-data.example.invalid/api"


def make_settings(password: str = "secret") -> WorkerSettings:
    return WorkerSettings(
        matriz_base_url="https://matriz.example.invalid",
        matriz_username="user",
        matriz_password=SecretStr(password),
        market_data_client_id="client-id",
        market_data_client_secret=SecretStr("client-secret"),
        market_data_audience="audience",
        market_data_auth0_token_url="https://auth.example.invalid/oauth/token",
        market_data_base_url=MARKET_DATA_BASE_URL,
        worker_heartbeat_seconds=HEARTBEAT,
        _env_file=None,  # pyright: ignore[reportCallIssue]
    )


class FakeGateway:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.connected = False
        self.closed = False

    def connect(self) -> None:
        if self.fail:
            raise GatewayError("bad credentials")
        self.connected = True

    def close(self) -> None:
        self.closed = True


class FakeMarketDataGateway:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.connected = False
        self.closed = False

    def connect(self) -> None:
        if self.fail:
            raise MarketDataGatewayError("market data unreachable")
        self.connected = True

    def get_quote(self, symbol: str) -> Quote | None:
        return Quote(symbol=symbol, last_price=Decimal("100.5"), received_at=datetime.now(UTC))

    def close(self) -> None:
        self.closed = True


async def test_runs_until_stop(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    gateway = FakeGateway()
    market_data = FakeMarketDataGateway()
    stop = asyncio.Event()
    task = asyncio.create_task(run(gateway, market_data, make_settings(), stop))

    await asyncio.sleep(HEARTBEAT * 10)
    assert not task.done()
    assert caplog.text.count("worker heartbeat") >= 2

    stop.set()
    assert await asyncio.wait_for(task, timeout=10) == 0
    assert gateway.closed
    assert market_data.closed


async def test_logs_initialization_result(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    gateway = FakeGateway()
    stop = asyncio.Event()
    stop.set()

    assert await run(gateway, FakeMarketDataGateway(), make_settings(), stop) == 0
    assert gateway.connected
    assert "matriz-client initialized (base_url=https://matriz.example.invalid)" in caplog.text
    assert "worker stopped" in caplog.text


async def test_initialization_failure_returns_1(caplog: pytest.LogCaptureFixture) -> None:
    gateway = FakeGateway(fail=True)
    market_data = FakeMarketDataGateway()

    assert await run(gateway, market_data, make_settings(), asyncio.Event()) == 1
    assert "matriz-client initialization failed: bad credentials" in caplog.text
    assert gateway.closed
    assert market_data.closed


async def test_market_data_initialized_and_closed_on_stop(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO)
    market_data = FakeMarketDataGateway()
    stop = asyncio.Event()
    stop.set()

    assert await run(FakeGateway(), market_data, make_settings(), stop) == 0
    assert market_data.connected
    assert market_data.closed
    assert f"market-data-client initialized (base_url={MARKET_DATA_BASE_URL})" in caplog.text


async def test_market_data_initialization_failure_returns_1(
    caplog: pytest.LogCaptureFixture,
) -> None:
    gateway = FakeGateway()
    market_data = FakeMarketDataGateway(fail=True)

    assert await run(gateway, market_data, make_settings(), asyncio.Event()) == 1
    assert "market-data-client initialization failed: market data unreachable" in caplog.text
    assert gateway.closed
    assert market_data.closed


async def test_matriz_failure_skips_market_data_connect() -> None:
    market_data = FakeMarketDataGateway()

    assert await run(FakeGateway(fail=True), market_data, make_settings(), asyncio.Event()) == 1
    assert market_data.connected is False


@pytest.mark.parametrize("sig", [signal.SIGINT, signal.SIGTERM])
async def test_signal_stops_with_zero(sig: signal.Signals) -> None:
    gateway = FakeGateway()
    market_data = FakeMarketDataGateway()
    task = asyncio.create_task(serve(gateway, market_data, make_settings()))
    await asyncio.sleep(HEARTBEAT * 5)

    os.kill(os.getpid(), sig)

    assert await asyncio.wait_for(task, timeout=10) == 0
    assert gateway.closed
    assert market_data.closed


def test_client_gateway_wraps_library_errors() -> None:
    # Credenciales vacías: matriz-client lanza AuthenticationError antes de cualquier I/O.
    gateway = MatrizClientGateway(make_settings(password=""))
    try:
        with pytest.raises(GatewayError):
            gateway.connect()
    finally:
        gateway.close()
