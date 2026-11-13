"""Endpoints de cuentas, instrumentos y órdenes con `FakeTrading` (EB-26..EB-28, EB-34..EB-36)."""

from collections.abc import Iterator

import pytest
from backend.main import create_app
from backend.matriz import NOT_CONFIGURED_DETAIL, InstrumentCache
from backend.settings import BackendSettings
from broker.matriz_gateway import GatewayError, InstrumentRef, NewOrder
from fake_trading import FakeTrading, make_order
from fastapi.testclient import TestClient
from pydantic import SecretStr

URL = "postgresql+psycopg://user:secret@localhost:5432/test"
DEV_ORIGIN = "http://localhost:5173"
ACCOUNTS = "REM1, REM2"
SECRET = "s3cr3t!pw"

LIMIT_BODY: dict[str, object] = {
    "account_id": "REM1",
    "symbol": "DLR/DIC26",
    "market_id": "ROFX",
    "side": "BUY",
    "order_type": "LIMIT",
    "quantity": 3,
    "price": 1000.5,
}


def make_settings(
    accounts: str = ACCOUNTS, username: str | None = None, password: str | None = None
) -> BackendSettings:
    # Todo explícito y sin `.env`: los tests no dependen de las credenciales locales.
    return BackendSettings(
        _env_file=None,  # pyright: ignore[reportCallIssue]
        database_url=URL,
        cors_origins=DEV_ORIGIN,
        matriz_accounts=accounts,
        matriz_username=username,
        matriz_password=SecretStr(password) if password is not None else None,
    )


@pytest.fixture
def fake() -> FakeTrading:
    return FakeTrading()


@pytest.fixture
def client(fake: FakeTrading) -> Iterator[TestClient]:
    with TestClient(create_app(make_settings(), trading=fake)) as test_client:
        yield test_client


# -- /accounts ---------------------------------------------------------------


def test_accounts_lists_configured_accounts(client: TestClient) -> None:
    response = client.get("/accounts")
    assert response.status_code == 200
    assert response.json() == {"accounts": ["REM1", "REM2"]}


def test_accounts_empty_when_not_configured(fake: FakeTrading) -> None:
    with TestClient(create_app(make_settings(accounts=""), trading=fake)) as client:
        response = client.get("/accounts")
    assert response.status_code == 200
    assert response.json() == {"accounts": []}


# -- /instruments ------------------------------------------------------------


def test_instruments_ok_and_cached(client: TestClient, fake: FakeTrading) -> None:
    fake.instruments = [InstrumentRef(symbol="DLR/DIC26", market_id="ROFX")]
    first = client.get("/instruments")
    second = client.get("/instruments")
    assert first.status_code == 200
    assert first.json() == [{"symbol": "DLR/DIC26", "market_id": "ROFX"}]
    assert second.json() == first.json()
    assert fake.list_instruments_calls == 1


def test_instruments_failure_is_502_and_not_cached(client: TestClient, fake: FakeTrading) -> None:
    fake.error = GatewayError("timeout")
    response = client.get("/instruments")
    assert response.status_code == 502
    assert response.json() == {"detail": "Matriz: timeout"}
    fake.error = None
    assert client.get("/instruments").status_code == 200
    assert fake.list_instruments_calls == 2


def test_instrument_cache_refreshes_after_ttl(fake: FakeTrading) -> None:
    now = [0.0]
    cache = InstrumentCache(fake, ttl_seconds=10.0, clock=lambda: now[0])
    cache.get()
    now[0] = 9.9
    cache.get()
    assert fake.list_instruments_calls == 1
    now[0] = 10.0
    cache.get()
    assert fake.list_instruments_calls == 2


# -- GET /orders -------------------------------------------------------------


def test_list_orders_sorted_desc_with_missing_time_last(
    client: TestClient, fake: FakeTrading
) -> None:
    fake.orders["REM1"] = [
        make_order(cl_ord_id="old", transact_time="20261112-09:00:00"),
        make_order(cl_ord_id="none", transact_time=None, price=None, ord_type="MARKET"),
        make_order(cl_ord_id="new", transact_time="20261112-11:00:00"),
    ]
    response = client.get("/orders", params={"account_id": "REM1"})
    assert response.status_code == 200
    body = response.json()
    assert [o["cl_ord_id"] for o in body] == ["new", "old", "none"]
    assert body[2]["price"] is None
    assert set(body[0]) == {
        "cl_ord_id",
        "proprietary",
        "account_id",
        "symbol",
        "market_id",
        "side",
        "ord_type",
        "order_qty",
        "price",
        "cum_qty",
        "leaves_qty",
        "status",
        "transact_time",
        "text",
    }
    assert fake.list_orders_calls == ["REM1"]


def test_list_orders_requires_account_id(client: TestClient) -> None:
    assert client.get("/orders").status_code == 422


def test_list_orders_rejects_unconfigured_account(client: TestClient, fake: FakeTrading) -> None:
    response = client.get("/orders", params={"account_id": "OTRA"})
    assert response.status_code == 422
    assert response.json() == {"detail": "Cuenta no configurada: OTRA"}
    assert fake.list_orders_calls == []


def test_list_orders_gateway_error_is_502_without_password(
    client: TestClient, fake: FakeTrading
) -> None:
    # El broker ya redacta la contraseña; el backend no agrega nada sensible.
    fake.error = GatewayError("401 Unauthorized for user=u password=***")
    response = client.get("/orders", params={"account_id": "REM1"})
    assert response.status_code == 502
    assert response.json()["detail"].startswith("Matriz: ")
    assert SECRET not in response.text


# -- POST /orders ------------------------------------------------------------


def test_create_limit_order_201(client: TestClient, fake: FakeTrading) -> None:
    response = client.post("/orders", json=LIMIT_BODY)
    assert response.status_code == 201
    assert response.json() == {"cl_ord_id": "ord-1", "proprietary": "PBCP"}
    assert fake.new_orders == [
        NewOrder(
            account_id="REM1",
            symbol="DLR/DIC26",
            market_id="ROFX",
            side="BUY",
            order_type="LIMIT",
            quantity=3,
            price=1000.5,
        )
    ]


def test_create_market_order_sends_no_price(client: TestClient, fake: FakeTrading) -> None:
    body = {k: v for k, v in LIMIT_BODY.items() if k != "price"} | {"order_type": "MARKET"}
    response = client.post("/orders", json=body)
    assert response.status_code == 201
    assert fake.new_orders[0].price is None  # EB-27


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"price": None}, "El precio es obligatorio para órdenes LIMIT"),  # EB-26
        ({"order_type": "MARKET"}, "Las órdenes MARKET no llevan precio"),  # EB-27
        ({"price": 0}, None),
        ({"price": -1}, None),
        ({"quantity": 1.5}, None),  # EB-28
        ({"quantity": 0}, None),
        ({"quantity": -1}, None),
        ({"quantity": "3"}, None),
        ({"quantity": None}, None),
        ({"order_type": "STOP_LIMIT"}, None),
        ({"side": "SHORT"}, None),
        ({"market_id": "XXX"}, None),
        ({"symbol": ""}, None),
        ({"time_in_force": "IOC"}, None),
    ],
)
def test_create_order_validation_422(
    client: TestClient, fake: FakeTrading, changes: dict[str, object], message: str | None
) -> None:
    response = client.post("/orders", json=LIMIT_BODY | changes)
    assert response.status_code == 422
    if message is not None:
        assert message in response.text
    assert fake.new_orders == []


def test_create_order_rejects_unconfigured_account(client: TestClient, fake: FakeTrading) -> None:
    response = client.post("/orders", json=LIMIT_BODY | {"account_id": "OTRA"})
    assert response.status_code == 422
    assert response.json() == {"detail": "Cuenta no configurada: OTRA"}
    assert fake.new_orders == []


def test_create_order_gateway_error_502(client: TestClient, fake: FakeTrading) -> None:
    fake.error = GatewayError("Orden rechazada")
    response = client.post("/orders", json=LIMIT_BODY)
    assert response.status_code == 502
    assert response.json() == {"detail": "Matriz: Orden rechazada"}


# -- POST /orders/cancel -----------------------------------------------------


def test_cancel_order_200(client: TestClient, fake: FakeTrading) -> None:
    response = client.post("/orders/cancel", json={"cl_ord_id": "ord-9", "proprietary": "PBCP"})
    assert response.status_code == 200
    assert response.json() == {"cl_ord_id": "ord-9", "proprietary": "PBCP"}
    assert fake.cancels == [("ord-9", "PBCP")]


def test_cancel_order_validation_422(client: TestClient, fake: FakeTrading) -> None:
    response = client.post("/orders/cancel", json={"cl_ord_id": "", "proprietary": "PBCP"})
    assert response.status_code == 422
    assert fake.cancels == []


def test_cancel_order_gateway_error_502(client: TestClient, fake: FakeTrading) -> None:
    fake.error = GatewayError("Orden inexistente")
    response = client.post("/orders/cancel", json={"cl_ord_id": "x", "proprietary": "PBCP"})
    assert response.status_code == 502
    assert response.json() == {"detail": "Matriz: Orden inexistente"}


# -- Sin credenciales (503) y salud intacta (UB-4) ---------------------------


def test_trading_without_credentials_is_503_and_health_still_works() -> None:
    app = create_app(make_settings())  # sin MATRIZ_USERNAME/MATRIZ_PASSWORD
    with TestClient(app) as client:
        for response in (
            client.get("/instruments"),
            client.get("/orders", params={"account_id": "REM1"}),
            client.post("/orders", json=LIMIT_BODY),
            client.post("/orders/cancel", json={"cl_ord_id": "x", "proprietary": "y"}),
        ):
            assert response.status_code == 503
            assert response.json() == {"detail": NOT_CONFIGURED_DETAIL}
        assert client.get("/accounts").status_code == 200
        assert client.get("/health").status_code in (200, 503)


def test_credentials_build_gateway_without_login() -> None:
    # Construir la app con credenciales no hace red: el login es diferido.
    app = create_app(make_settings(username="u", password=SECRET))
    assert app.state.trading is not None


# -- CORS (EB-36) y OpenAPI (EB-34) ------------------------------------------


def test_cors_preflight_allows_post(client: TestClient) -> None:
    for path in ("/orders", "/orders/cancel"):
        response = client.options(
            path,
            headers={
                "Origin": DEV_ORIGIN,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == DEV_ORIGIN
        assert "POST" in response.headers["access-control-allow-methods"]


def test_openapi_exposes_trading_operations(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]
    operations = {
        ("/accounts", "get"): "listAccounts",
        ("/instruments", "get"): "listInstruments",
        ("/orders", "get"): "listOrders",
        ("/orders", "post"): "createOrder",
        ("/orders/cancel", "post"): "cancelOrder",
    }
    for (path, method), operation_id in operations.items():
        assert paths[path][method]["operationId"] == operation_id
    assert "201" in paths["/orders"]["post"]["responses"]
