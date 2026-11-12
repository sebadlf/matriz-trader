"""Tests del adaptador de market-data-client sin red (AC-12)."""

from collections.abc import Callable

import httpx
import pytest
from pydantic import SecretStr
from worker.market_data_gateway import MarketDataClientGateway, MarketDataGatewayError
from worker.settings import WorkerSettings

BASE_URL = "https://md.example.invalid/api"


def make_settings() -> WorkerSettings:
    return WorkerSettings(
        matriz_base_url="https://matriz.example.invalid",
        matriz_username="user",
        matriz_password=SecretStr("secret"),
        market_data_client_id="client-id",
        market_data_client_secret=SecretStr("md-secret"),
        market_data_audience="audience",
        market_data_auth0_token_url="https://auth.example.invalid/oauth/token",
        market_data_base_url=BASE_URL,
        _env_file=None,  # pyright: ignore[reportCallIssue]
    )


def make_gateway(
    handler: Callable[[httpx.Request], httpx.Response],
) -> MarketDataClientGateway:
    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    return MarketDataClientGateway(make_settings(), http_client=http_client, max_retries=0)


def test_connect_error_is_translated_to_gateway_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    gateway = make_gateway(handler)
    try:
        with pytest.raises(MarketDataGatewayError):
            gateway.connect()
    finally:
        gateway.close()


def test_connect_with_healthy_api_does_not_raise() -> None:
    requested: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested.append(request.url.path)
        return httpx.Response(
            200,
            json={
                "status": "ok",
                "auth": {"configured": True, "enabled": True, "issuer": "x"},
            },
        )

    gateway = make_gateway(handler)
    try:
        gateway.connect()
    finally:
        gateway.close()

    assert requested == ["/api/health"]
