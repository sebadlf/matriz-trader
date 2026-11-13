"""Adaptador tipado sobre `matriz-client`: sesión (worker) y operación de órdenes (backend).

Es el único módulo del repo que importa `matriz_client`. No usar para market data:
ver `worker.market_data_gateway`. Expone solo tipos propios del repo.
"""

import threading
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal, Protocol

import httpx
from matriz_client import AuthenticationError, Client, MatrizClientError

Side = Literal["BUY", "SELL"]
OrderKind = Literal["MARKET", "LIMIT"]

REDACTED = "***"


class GatewayError(Exception):
    """Fallo de Matriz (`MatrizClientError` | `httpx.HTTPError`) con mensaje sin secretos."""


@dataclass(frozen=True)
class MatrizCredentials:
    base_url: str
    username: str
    password: str


@dataclass(frozen=True)
class InstrumentRef:
    symbol: str
    market_id: str


@dataclass(frozen=True)
class OrderRecord:
    cl_ord_id: str | None
    proprietary: str | None
    account_id: str | None
    symbol: str | None
    market_id: str | None
    side: str | None
    ord_type: str | None
    order_qty: float | None
    price: float | None
    cum_qty: float | None
    leaves_qty: float | None
    # str libre: valores fuera del enum se muestran tal cual.
    status: str | None
    transact_time: str | None
    text: str | None


@dataclass(frozen=True)
class NewOrder:
    account_id: str
    symbol: str
    market_id: str
    side: Side
    order_type: OrderKind
    quantity: int
    # None si MARKET: no se envía precio a Matriz.
    price: float | None


@dataclass(frozen=True)
class OrderAck:
    cl_ord_id: str
    proprietary: str


class MatrizGateway(Protocol):
    """Sesión con Matriz (la usa el worker)."""

    def connect(self) -> None:
        """Conecta y autentica; lanza `GatewayError` si falla."""
        ...

    def close(self) -> None: ...


class MatrizTrading(Protocol):
    """Operación de órdenes (la usa el backend). Todo fallo es `GatewayError`."""

    def list_orders(self, account_id: str) -> list[OrderRecord]: ...

    def new_order(self, order: NewOrder) -> OrderAck: ...

    def cancel_order(self, cl_ord_id: str, proprietary: str) -> OrderAck: ...

    def list_instruments(self) -> list[InstrumentRef]: ...


class MatrizClientGateway:
    """Implementa `MatrizGateway` y `MatrizTrading` con un `Client` compartido.

    El login es diferido (primer uso) y único, protegido por un lock; si Matriz
    rechaza la autenticación, el próximo uso vuelve a intentar el login.
    """

    def __init__(self, credentials: MatrizCredentials) -> None:
        self._password = credentials.password
        # Credenciales siempre explícitas: con `None` la librería cae a `PRIMARY_*` del entorno.
        # Construir el `Client` no hace I/O.
        self._client = Client(
            base_url=credentials.base_url,
            username=credentials.username,
            password=credentials.password,
        )
        self._lock = threading.Lock()
        self._logged_in = False

    # -- Sesión ------------------------------------------------------------

    def connect(self) -> None:
        self._ensure_session()

    def close(self) -> None:
        self._client.close()

    # -- Operación -----------------------------------------------------------

    def list_orders(self, account_id: str) -> list[OrderRecord]:
        orders = self._call(lambda: self._client.get_all_orders(account_id))
        return [
            OrderRecord(
                cl_ord_id=order.clOrdId,
                proprietary=order.proprietary,
                account_id=order.accountId,
                symbol=order.instrumentId.symbol,
                market_id=order.instrumentId.marketId,
                side=order.side,
                ord_type=order.ordType,
                order_qty=order.orderQty,
                price=order.price,
                cum_qty=order.cumQty,
                leaves_qty=order.leavesQty,
                status=order.status,
                transact_time=order.transactTime,
                text=order.text,
            )
            for order in orders
        ]

    def new_order(self, order: NewOrder) -> OrderAck:
        # Sin time_in_force, iceberg, display_qty, cancel_previous ni expire_date:
        # quedan los defaults de la librería.
        price = order.price if order.order_type == "LIMIT" else None
        response = self._call(
            lambda: self._client.new_order(
                order.symbol,
                order.side,
                order.quantity,
                order.account_id,
                price,
                order_type=order.order_type,
                market_id=_market_id(order.market_id),
            )
        )
        return _ack(response.clientId, response.proprietary)

    def cancel_order(self, cl_ord_id: str, proprietary: str) -> OrderAck:
        response = self._call(lambda: self._client.cancel_order(cl_ord_id, proprietary))
        return _ack(response.clientId, response.proprietary)

    def list_instruments(self) -> list[InstrumentRef]:
        instruments = self._call(self._client.get_all_instruments)
        refs = [
            InstrumentRef(symbol=symbol, market_id=market_id)
            for instrument in instruments
            if (symbol := instrument.instrumentId.symbol) is not None
            and (market_id := instrument.instrumentId.marketId) is not None
        ]
        return sorted(refs, key=lambda ref: ref.symbol)

    # -- Internos ------------------------------------------------------------

    def _ensure_session(self) -> None:
        with self._lock:
            if self._logged_in:
                return
            # `Client` no tiene `connect()`: `login()` valida las credenciales contra la API.
            try:
                self._client.login()
            except (MatrizClientError, httpx.HTTPError) as exc:
                raise self._error(exc) from exc
            self._logged_in = True

    def _call[T](self, operation: Callable[[], T]) -> T:
        self._ensure_session()
        try:
            return operation()
        except AuthenticationError as exc:
            with self._lock:
                self._logged_in = False
            raise self._error(exc) from exc
        except (MatrizClientError, httpx.HTTPError) as exc:
            raise self._error(exc) from exc

    def _error(self, exc: Exception) -> GatewayError:
        message = str(exc) or type(exc).__name__
        if self._password:
            message = message.replace(self._password, REDACTED)
        return GatewayError(message)


def _market_id(value: str) -> Literal["ROFX"]:
    if value != "ROFX":
        raise GatewayError(f"Mercado no soportado: {value}")
    return value


def _ack(cl_ord_id: str | None, proprietary: str | None) -> OrderAck:
    if cl_ord_id is None or proprietary is None:
        raise GatewayError("Matriz no devolvió el identificador de la orden")
    return OrderAck(cl_ord_id=cl_ord_id, proprietary=proprietary)
