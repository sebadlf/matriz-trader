"""Tests de `broker.matriz_gateway` con un `Client` falso (sin red ni credenciales reales)."""

from dataclasses import dataclass, field
from typing import Any

import httpx
import pytest
from broker.matriz_gateway import (
    GatewayError,
    InstrumentRef,
    MatrizClientGateway,
    MatrizCredentials,
    NewOrder,
    OrderAck,
    OrderRecord,
)

from broker import matriz_gateway

PASSWORD = "s3cr3t-pass"


@dataclass
class FakeInstrumentId:
    symbol: str | None = None
    marketId: str | None = None


@dataclass
class FakeOrder:
    clOrdId: str | None = None
    proprietary: str | None = None
    accountId: str | None = None
    instrumentId: FakeInstrumentId = field(default_factory=FakeInstrumentId)
    price: float | None = None
    orderQty: float | None = None
    ordType: str | None = None
    side: str | None = None
    timeInForce: str | None = None
    transactTime: str | None = None
    cumQty: float | None = None
    leavesQty: float | None = None
    avgPx: float | None = None
    status: str | None = None
    text: str | None = None


@dataclass
class FakeInstrument:
    instrumentId: FakeInstrumentId


@dataclass
class FakeResponse:
    clientId: str | None
    proprietary: str | None


class FakeClient:
    """Imita la superficie del `Client` de Matriz que usa el gateway."""

    instances: list["FakeClient"] = []  # noqa: RUF012

    def __init__(self, *, base_url: str, username: str, password: str) -> None:
        self.init_kwargs = {"base_url": base_url, "username": username, "password": password}
        self.logins = 0
        self.closed = False
        self.orders: list[FakeOrder] = []
        self.instruments: list[FakeInstrument] = []
        self.response = FakeResponse(clientId="cl-1", proprietary="PBCP")
        self.new_order_calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
        self.cancel_calls: list[tuple[str, str]] = []
        self.error: Exception | None = None
        FakeClient.instances.append(self)

    def login(self) -> str:
        self.logins += 1
        return "token"

    def close(self) -> None:
        self.closed = True

    def _maybe_fail(self) -> None:
        if self.error is not None:
            raise self.error

    def get_all_orders(self, account_id: str) -> list[FakeOrder]:
        self._maybe_fail()
        return [o for o in self.orders if o.accountId == account_id]

    def get_all_instruments(self) -> list[FakeInstrument]:
        self._maybe_fail()
        return self.instruments

    def new_order(self, *args: Any, **kwargs: Any) -> FakeResponse:
        self._maybe_fail()
        self.new_order_calls.append((args, kwargs))
        return self.response

    def cancel_order(self, cl_ord_id: str, proprietary: str) -> FakeResponse:
        self._maybe_fail()
        self.cancel_calls.append((cl_ord_id, proprietary))
        return self.response


@pytest.fixture(autouse=True)
def fake_client(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeClient.instances = []
    monkeypatch.setattr(matriz_gateway, "Client", FakeClient)


def make_gateway() -> tuple[MatrizClientGateway, FakeClient]:
    credentials = MatrizCredentials(
        base_url="https://matriz.example.invalid", username="u", password=PASSWORD
    )
    gateway = MatrizClientGateway(credentials)
    return gateway, FakeClient.instances[-1]


def make_order(order_type: matriz_gateway.OrderKind, price: float | None) -> NewOrder:
    return NewOrder(
        account_id="REM1",
        symbol="DLR/DIC26",
        market_id="ROFX",
        side="BUY",
        order_type=order_type,
        quantity=3,
        price=price,
    )


def test_constructor_passes_explicit_credentials_without_login() -> None:
    _, fake = make_gateway()
    assert fake.init_kwargs == {
        "base_url": "https://matriz.example.invalid",
        "username": "u",
        "password": PASSWORD,
    }
    assert fake.logins == 0


def test_login_happens_once_across_operations() -> None:
    gateway, fake = make_gateway()
    gateway.connect()
    gateway.list_orders("REM1")
    gateway.list_instruments()
    gateway.cancel_order("cl-1", "PBCP")
    assert fake.logins == 1
    gateway.close()
    assert fake.closed


def test_list_orders_maps_order_fields() -> None:
    gateway, fake = make_gateway()
    fake.orders = [
        FakeOrder(
            clOrdId="cl-9",
            proprietary="PBCP",
            accountId="REM1",
            instrumentId=FakeInstrumentId(symbol="DLR/DIC26", marketId="ROFX"),
            price=None,
            orderQty=5.0,
            ordType="MARKET",
            side="SELL",
            transactTime="20261112-10:00:00.000-0300",
            cumQty=2.0,
            leavesQty=3.0,
            status="PARTIALLY_FILLED",
            text="ok",
        ),
        FakeOrder(accountId="OTHER"),
    ]
    assert gateway.list_orders("REM1") == [
        OrderRecord(
            cl_ord_id="cl-9",
            proprietary="PBCP",
            account_id="REM1",
            symbol="DLR/DIC26",
            market_id="ROFX",
            side="SELL",
            ord_type="MARKET",
            order_qty=5.0,
            price=None,
            cum_qty=2.0,
            leaves_qty=3.0,
            status="PARTIALLY_FILLED",
            transact_time="20261112-10:00:00.000-0300",
            text="ok",
        )
    ]


def test_new_order_market_sends_price_none_and_only_type_and_market_kwargs() -> None:
    gateway, fake = make_gateway()
    ack = gateway.new_order(make_order("MARKET", price=12.5))
    assert ack == OrderAck(cl_ord_id="cl-1", proprietary="PBCP")
    assert fake.new_order_calls == [
        (("DLR/DIC26", "BUY", 3, "REM1", None), {"order_type": "MARKET", "market_id": "ROFX"})
    ]


def test_new_order_limit_sends_price() -> None:
    gateway, fake = make_gateway()
    gateway.new_order(make_order("LIMIT", price=1010.5))
    args, kwargs = fake.new_order_calls[0]
    assert args == ("DLR/DIC26", "BUY", 3, "REM1", 1010.5)
    assert set(kwargs) == {"order_type", "market_id"}
    assert kwargs["order_type"] == "LIMIT"


def test_missing_identifier_in_response_is_gateway_error() -> None:
    gateway, fake = make_gateway()
    fake.response = FakeResponse(clientId=None, proprietary="PBCP")
    with pytest.raises(GatewayError, match="identificador"):
        gateway.new_order(make_order("MARKET", price=None))


def test_cancel_order_passes_identifiers() -> None:
    gateway, fake = make_gateway()
    assert gateway.cancel_order("cl-7", "PBCP") == OrderAck(cl_ord_id="cl-1", proprietary="PBCP")
    assert fake.cancel_calls == [("cl-7", "PBCP")]


def test_list_instruments_drops_incomplete_and_sorts_by_symbol() -> None:
    gateway, fake = make_gateway()
    fake.instruments = [
        FakeInstrument(FakeInstrumentId(symbol="ZZZ", marketId="ROFX")),
        FakeInstrument(FakeInstrumentId(symbol=None, marketId="ROFX")),
        FakeInstrument(FakeInstrumentId(symbol="AAA", marketId=None)),
        FakeInstrument(FakeInstrumentId(symbol="DLR/DIC26", marketId="ROFX")),
    ]
    assert gateway.list_instruments() == [
        InstrumentRef(symbol="DLR/DIC26", market_id="ROFX"),
        InstrumentRef(symbol="ZZZ", market_id="ROFX"),
    ]


def test_errors_are_wrapped_and_password_is_redacted() -> None:
    gateway, fake = make_gateway()
    fake.error = httpx.ConnectError(f"fallo con password={PASSWORD}")
    with pytest.raises(GatewayError) as excinfo:
        gateway.list_orders("REM1")
    assert PASSWORD not in str(excinfo.value)
    assert "***" in str(excinfo.value)
