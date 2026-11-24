"""Conversiones y spread de market data en el dominio (AC-3, AC-4, AC-5, AC-8, AC-9, AC-10)."""

import json
from datetime import UTC, datetime
from decimal import Context, Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import TypeAdapter, ValidationError

from app.domain.errors import DomainError, MarketDataUnavailableError
from app.domain.market_data import (
    SPREAD_QUANT,
    epoch_ms_to_utc,
    epoch_s_to_utc,
    spread_pct,
    to_decimal,
)
from app.domain.numeric import MarketDecimal, Percent

EXAMPLES = 200

positive_prices = st.decimals(
    min_value=Decimal("0.00000001"),
    max_value=Decimal("1e12"),
    allow_nan=False,
    allow_infinity=False,
    places=8,
)
MARKET_DECIMAL_ADAPTER: TypeAdapter[Decimal] = TypeAdapter(MarketDecimal)
PERCENT_ADAPTER: TypeAdapter[Decimal] = TypeAdapter(Percent)


# --- to_decimal (AC-3, AC-5) ---------------------------------------------------------


@settings(max_examples=EXAMPLES)
@given(st.floats(allow_nan=False, allow_infinity=False))
def test_to_decimal_goes_through_str(value: float) -> None:
    assert to_decimal(value) == Decimal(str(value))


def test_to_decimal_avoids_binary_float_expansion() -> None:
    assert to_decimal(0.1) == Decimal("0.1")
    assert str(to_decimal(0.1)) == "0.1"


@settings(max_examples=EXAMPLES)
@given(st.integers(min_value=-(10**15), max_value=10**15))
def test_to_decimal_accepts_ints(value: int) -> None:
    assert to_decimal(value) == Decimal(value)


@pytest.mark.parametrize("value", [None, float("nan"), float("inf"), float("-inf")])
def test_to_decimal_missing_or_non_finite_is_none(value: float | None) -> None:
    assert to_decimal(value) is None


def test_to_decimal_zero_is_zero_not_none() -> None:
    assert to_decimal(0.0) == Decimal("0.0")


# --- fechas (AC-4) -------------------------------------------------------------------


def test_epoch_ms_to_utc_keeps_milliseconds() -> None:
    result = epoch_ms_to_utc(1_795_528_991_250)
    assert result == datetime(2026, 11, 24, 14, 3, 11, 250_000, tzinfo=UTC)
    assert result is not None
    assert result.tzinfo is UTC


def test_epoch_ms_to_utc_none_is_none() -> None:
    assert epoch_ms_to_utc(None) is None


@settings(max_examples=EXAMPLES)
@given(st.integers(min_value=0, max_value=4_102_444_800_000))
def test_epoch_ms_to_utc_roundtrip(value: int) -> None:
    result = epoch_ms_to_utc(value)
    assert result is not None
    assert result.tzinfo is UTC
    delta = result - datetime(1970, 1, 1, tzinfo=UTC)
    assert delta.days * 86_400_000 + delta.seconds * 1000 + delta.microseconds // 1000 == value


def test_epoch_s_to_utc_is_utc() -> None:
    result = epoch_s_to_utc(1_795_528_991.25)
    assert result == datetime(2026, 11, 24, 14, 3, 11, 250_000, tzinfo=UTC)
    assert result.tzinfo is UTC
    assert result.isoformat() == "2026-11-24T14:03:11.250000+00:00"


# --- spread_pct (AC-8, AC-9, AC-10) --------------------------------------------------


@pytest.mark.parametrize(
    ("bid", "ask", "expected"),
    [
        ("100", "101", "0.9950"),
        ("100", "100", "0.0000"),
        ("99.5", "100.5", "1.0000"),
        ("1", "3", "100.0000"),
        ("101", "100", "-0.9950"),
    ],
)
def test_spread_pct_known_values(bid: str, ask: str, expected: str) -> None:
    result = spread_pct(Decimal(bid), Decimal(ask))
    assert result == Decimal(expected)
    assert result is not None
    assert result.as_tuple().exponent == -4


def test_spread_pct_rounds_half_even() -> None:
    # Precio medio 2 000 000: diferencia d → spread exacto d * 0.00005.
    # 0.00005 → 0.0000 (par), no 0.0001.
    assert spread_pct(Decimal("1999999.5"), Decimal("2000000.5")) == Decimal("0.0000")
    # 0.00015 → 0.0002 (par).
    assert spread_pct(Decimal("1999998.5"), Decimal("2000001.5")) == Decimal("0.0002")
    # 0.00025 → 0.0002 (par), no 0.0003.
    assert spread_pct(Decimal("1999997.5"), Decimal("2000002.5")) == Decimal("0.0002")
    # Libro cruzado: -0.00025 → -0.0002.
    assert spread_pct(Decimal("2000002.5"), Decimal("1999997.5")) == Decimal("-0.0002")


@pytest.mark.parametrize(
    ("bid", "ask"),
    [
        (None, Decimal(100)),
        (Decimal(100), None),
        (None, None),
        (Decimal(0), Decimal(100)),
        (Decimal(100), Decimal(0)),
        (Decimal(-1), Decimal(100)),
        (Decimal(100), Decimal("-0.5")),
    ],
)
def test_spread_pct_null_when_missing_or_non_positive(
    bid: Decimal | None, ask: Decimal | None
) -> None:
    assert spread_pct(bid, ask) is None


def test_spread_pct_crossed_book_is_negative() -> None:
    result = spread_pct(Decimal(105), Decimal(100))
    assert result is not None
    assert result < 0


@settings(max_examples=EXAMPLES)
@given(positive_prices, positive_prices)
def test_spread_pct_matches_reference(bid: Decimal, ask: Decimal) -> None:
    result = spread_pct(bid, ask)
    assert result is not None
    assert result.as_tuple().exponent == -4
    wide = Context(prec=60)
    exact = wide.multiply(wide.divide(ask - bid, wide.divide(ask + bid, 2)), 100)
    assert abs(result - exact) <= SPREAD_QUANT / 2
    assert Decimal(-200) <= result <= Decimal(200)


@settings(max_examples=EXAMPLES)
@given(positive_prices, positive_prices)
def test_spread_pct_is_antisymmetric(bid: Decimal, ask: Decimal) -> None:
    forward = spread_pct(bid, ask)
    backward = spread_pct(ask, bid)
    assert forward is not None
    assert backward is not None
    assert backward == -forward
    assert (forward < 0) == (ask < bid)


# --- tipos de esquema y error --------------------------------------------------------


def test_market_decimal_allows_negative_and_serializes_as_string() -> None:
    value = MARKET_DECIMAL_ADAPTER.validate_python(Decimal("-12.123456789012"))
    assert json.loads(MARKET_DECIMAL_ADAPTER.dump_json(value)) == "-12.123456789012"


def test_market_decimal_rejects_nan() -> None:
    with pytest.raises(ValidationError):
        MARKET_DECIMAL_ADAPTER.validate_python(Decimal("NaN"))


def test_percent_serializes_as_string_and_limits_places() -> None:
    value = PERCENT_ADAPTER.validate_python(Decimal("-0.9950"))
    assert json.loads(PERCENT_ADAPTER.dump_json(value)) == "-0.9950"
    with pytest.raises(ValidationError):
        PERCENT_ADAPTER.validate_python(Decimal("0.12345"))


def test_market_data_unavailable_error_is_502_domain_error() -> None:
    error = MarketDataUnavailableError("sin datos")
    assert isinstance(error, DomainError)
    assert error.status == 502
    assert error.title == "Market data no disponible"
    assert error.detail == "sin datos"
