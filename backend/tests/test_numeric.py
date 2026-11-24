"""Propiedades de los tipos numéricos del dominio con Hypothesis (AC-51, AC-53)."""

import json
from decimal import ROUND_HALF_EVEN, Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import TypeAdapter

from app.domain.numeric import DECIMAL_CONTEXT, Money, Price, round_to_tick

EXAMPLES = 200

prices = st.decimals(
    min_value=Decimal(0),
    max_value=Decimal("1e12"),
    allow_nan=False,
    allow_infinity=False,
    places=8,
)
ticks = st.decimals(
    min_value=Decimal("0.00000001"),
    max_value=Decimal(1000),
    allow_nan=False,
    allow_infinity=False,
    places=8,
)
# Money admite 24 dígitos con 8 decimales: |m| < 10^16.
money = st.decimals(
    min_value=Decimal("-9999999999999999.99999999"),
    max_value=Decimal("9999999999999999.99999999"),
    allow_nan=False,
    allow_infinity=False,
    places=8,
)
MONEY_ADAPTER: TypeAdapter[Decimal] = TypeAdapter(Money)


def test_decimal_context_rounds_half_even() -> None:
    assert DECIMAL_CONTEXT.rounding == ROUND_HALF_EVEN


@settings(max_examples=EXAMPLES)
@given(price=prices, tick=ticks)
def test_round_to_tick_is_idempotent(price: Decimal, tick: Decimal) -> None:
    once = round_to_tick(price, tick)
    assert round_to_tick(once, tick) == once
    assert once % tick == 0


@settings(max_examples=EXAMPLES)
@given(a=money, b=money)
def test_money_sum_is_commutative(a: Decimal, b: Decimal) -> None:
    assert a + b == b + a


@settings(max_examples=EXAMPLES)
@given(m=money)
def test_money_json_roundtrip_has_no_precision_loss(m: Decimal) -> None:
    raw = MONEY_ADAPTER.dump_json(m)
    assert isinstance(json.loads(raw), str)
    assert MONEY_ADAPTER.validate_json(raw) == m


def test_round_to_tick_uses_half_even() -> None:
    assert round_to_tick(Decimal("0.25"), Decimal("0.5")) == Decimal("0.0")
    assert round_to_tick(Decimal("0.75"), Decimal("0.5")) == Decimal("1.0")


@pytest.mark.parametrize("tick", [Decimal(0), Decimal("-0.01")])
def test_round_to_tick_rejects_non_positive_tick(tick: Decimal) -> None:
    with pytest.raises(ValueError, match="tick debe ser > 0"):
        round_to_tick(Decimal(1), tick)


def test_price_rejects_negative_and_serializes_as_string() -> None:
    adapter: TypeAdapter[Decimal] = TypeAdapter(Price)
    assert adapter.dump_json(Decimal("1.50000000")) == b'"1.50000000"'
    with pytest.raises(ValueError, match="greater than or equal to 0"):
        adapter.validate_python(Decimal(-1))
