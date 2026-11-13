"""Endpoints de cuentas, instrumentos y órdenes contra Matriz (EB-34).

Todos son `def` (sync → threadpool de FastAPI). Los fallos de Matriz (`GatewayError`) se
traducen a `502` en `backend.matriz`; sin credenciales, `503`; validación, `422` (EB-35).
"""

from typing import Annotated, Literal, Self

from broker.matriz_gateway import MatrizTrading, NewOrder, OrderAck, OrderRecord
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

from backend.matriz import (
    InstrumentCache,
    get_accounts,
    get_instrument_cache,
    get_trading,
    require_configured_account,
)

router = APIRouter()

Trading = Annotated[MatrizTrading, Depends(get_trading)]
Accounts = Annotated[list[str], Depends(get_accounts)]
Instruments = Annotated[InstrumentCache, Depends(get_instrument_cache)]


class AccountsResponse(BaseModel):
    # Orden de `MATRIZ_ACCOUNTS`; `[]` si no hay cuentas configuradas (EB-21).
    accounts: list[str]


class InstrumentOut(BaseModel):
    symbol: str
    market_id: str


class OrderOut(BaseModel):
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
    status: str | None
    transact_time: str | None
    text: str | None


class NewOrderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    market_id: Literal["ROFX"]
    side: Literal["BUY", "SELL"]
    order_type: Literal["MARKET", "LIMIT"]
    # StrictInt: 1.5, "3" o true → 422 (EB-28).
    quantity: StrictInt = Field(gt=0)
    price: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def _price_matches_type(self) -> Self:
        if self.order_type == "LIMIT" and self.price is None:
            raise ValueError("El precio es obligatorio para órdenes LIMIT")  # EB-26
        if self.order_type == "MARKET" and self.price is not None:
            raise ValueError("Las órdenes MARKET no llevan precio")  # EB-27
        return self


class CancelOrderRequest(BaseModel):
    cl_ord_id: str = Field(min_length=1)
    proprietary: str = Field(min_length=1)


class OrderAckOut(BaseModel):
    cl_ord_id: str
    proprietary: str


def _order_out(order: OrderRecord) -> OrderOut:
    return OrderOut(
        cl_ord_id=order.cl_ord_id,
        proprietary=order.proprietary,
        account_id=order.account_id,
        symbol=order.symbol,
        market_id=order.market_id,
        side=order.side,
        ord_type=order.ord_type,
        order_qty=order.order_qty,
        price=order.price,
        cum_qty=order.cum_qty,
        leaves_qty=order.leaves_qty,
        status=order.status,
        transact_time=order.transact_time,
        text=order.text,
    )


def _ack_out(ack: OrderAck) -> OrderAckOut:
    return OrderAckOut(cl_ord_id=ack.cl_ord_id, proprietary=ack.proprietary)


@router.get("/accounts", operation_id="listAccounts")
def list_accounts(accounts: Accounts) -> AccountsResponse:
    return AccountsResponse(accounts=accounts)


@router.get("/instruments", operation_id="listInstruments")
def list_instruments(cache: Instruments) -> list[InstrumentOut]:
    return [InstrumentOut(symbol=ref.symbol, market_id=ref.market_id) for ref in cache.get()]


@router.get("/orders", operation_id="listOrders")
def list_orders(
    trading: Trading, accounts: Accounts, account_id: Annotated[str, Query(min_length=1)]
) -> list[OrderOut]:
    require_configured_account(account_id, accounts)
    records = trading.list_orders(account_id)
    # `transact_time` descendente (comparación de string); sin hora, al final.
    timed = sorted(
        (r for r in records if r.transact_time is not None),
        key=lambda r: r.transact_time or "",
        reverse=True,
    )
    untimed = [r for r in records if r.transact_time is None]
    return [_order_out(r) for r in [*timed, *untimed]]


@router.post("/orders", operation_id="createOrder", status_code=status.HTTP_201_CREATED)
def create_order(trading: Trading, accounts: Accounts, body: NewOrderRequest) -> OrderAckOut:
    require_configured_account(body.account_id, accounts)
    ack = trading.new_order(
        NewOrder(
            account_id=body.account_id,
            symbol=body.symbol,
            market_id=body.market_id,
            side=body.side,
            order_type=body.order_type,
            quantity=body.quantity,
            price=body.price,
        )
    )
    return _ack_out(ack)


@router.post("/orders/cancel", operation_id="cancelOrder")
def cancel_order(trading: Trading, body: CancelOrderRequest) -> OrderAckOut:
    return _ack_out(trading.cancel_order(body.cl_ord_id, body.proprietary))
