"""Tests del loop, señales y gateway del worker sin red (AC-14, AC-15, AC-17, AC-36)."""

import asyncio
import logging
import os
import signal

import pytest
from pydantic import SecretStr
from worker.matriz_gateway import GatewayError, MatrizClientGateway
from worker.runner import run, serve
from worker.settings import WorkerSettings

HEARTBEAT = 0.01


def make_settings(password: str = "secret") -> WorkerSettings:
    return WorkerSettings(
        matriz_base_url="https://matriz.example.invalid",
        matriz_username="user",
        matriz_password=SecretStr(password),
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


async def test_runs_until_stop(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    gateway = FakeGateway()
    stop = asyncio.Event()
    task = asyncio.create_task(run(gateway, make_settings(), stop))

    await asyncio.sleep(HEARTBEAT * 10)
    assert not task.done()
    assert caplog.text.count("worker heartbeat") >= 2

    stop.set()
    assert await asyncio.wait_for(task, timeout=10) == 0
    assert gateway.closed


async def test_logs_initialization_result(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    gateway = FakeGateway()
    stop = asyncio.Event()
    stop.set()

    assert await run(gateway, make_settings(), stop) == 0
    assert gateway.connected
    assert "matriz-client initialized (base_url=https://matriz.example.invalid)" in caplog.text
    assert "worker stopped" in caplog.text


async def test_initialization_failure_returns_1(caplog: pytest.LogCaptureFixture) -> None:
    gateway = FakeGateway(fail=True)

    assert await run(gateway, make_settings(), asyncio.Event()) == 1
    assert "matriz-client initialization failed: bad credentials" in caplog.text
    assert gateway.closed


@pytest.mark.parametrize("sig", [signal.SIGINT, signal.SIGTERM])
async def test_signal_stops_with_zero(sig: signal.Signals) -> None:
    gateway = FakeGateway()
    task = asyncio.create_task(serve(gateway, make_settings()))
    await asyncio.sleep(HEARTBEAT * 5)

    os.kill(os.getpid(), sig)

    assert await asyncio.wait_for(task, timeout=10) == 0
    assert gateway.closed


def test_client_gateway_wraps_library_errors() -> None:
    # Credenciales vacías: matriz-client lanza AuthenticationError antes de cualquier I/O.
    gateway = MatrizClientGateway(make_settings(password=""))
    try:
        with pytest.raises(GatewayError):
            gateway.connect()
    finally:
        gateway.close()
