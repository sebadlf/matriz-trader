"""`MatrizTrading` en memoria para tests del backend, sin red ni credenciales (EB-39)."""

from dataclasses import dataclass, field

from broker.matriz_gateway import GatewayError, InstrumentRef, NewOrder, OrderAck, OrderRecord


def make_order(**overrides: object) -> OrderRecord:
    values: dict[str, object] = {
        "cl_ord_id": "ord-1",
        "proprietary": "PBCP",
        "account_id": "REM1",
        "symbol": "DLR/DIC26",
        "market_id": "ROFX",
        "side": "BUY",
        "ord_type": "LIMIT",
        "order_qty": 10.0,
        "price": 1000.5,
        "cum_qty": 0.0,
        "leaves_qty": 10.0,
        "status": "NEW",
        "transact_time": "20261112-10:00:00.000-0300",
        "text": None,
    }
    values.update(overrides)
    return OrderRecord(**values)  # pyright: ignore[reportArgumentType]


@dataclass
class FakeTrading:
    """Guarda las llamadas; si `error` está seteado, toda operación lanza `GatewayError`."""

    orders: dict[str, list[OrderRecord]] = field(default_factory=dict[str, list[OrderRecord]])
    instruments: list[InstrumentRef] = field(default_factory=list[InstrumentRef])
    error: GatewayError | None = None
    list_orders_calls: list[str] = field(default_factory=list[str])
    new_orders: list[NewOrder] = field(default_factory=list[NewOrder])
    cancels: list[tuple[str, str]] = field(default_factory=list[tuple[str, str]])
    list_instruments_calls: int = 0

    def list_orders(self, account_id: str) -> list[OrderRecord]:
        self.list_orders_calls.append(account_id)
        self._maybe_fail()
        return list(self.orders.get(account_id, []))

    def new_order(self, order: NewOrder) -> OrderAck:
        self.new_orders.append(order)
        self._maybe_fail()
        return OrderAck(cl_ord_id=f"ord-{len(self.new_orders)}", proprietary="PBCP")

    def cancel_order(self, cl_ord_id: str, proprietary: str) -> OrderAck:
        self.cancels.append((cl_ord_id, proprietary))
        self._maybe_fail()
        return OrderAck(cl_ord_id=cl_ord_id, proprietary=proprietary)

    def list_instruments(self) -> list[InstrumentRef]:
        self.list_instruments_calls += 1
        self._maybe_fail()
        return list(self.instruments)

    def _maybe_fail(self) -> None:
        if self.error is not None:
            raise self.error
