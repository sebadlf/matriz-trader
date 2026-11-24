"""Conversiones y cálculos puros sobre la market data (sin I/O ni dependencias externas).

La librería de market data entrega `float` y epochs; acá se convierten a `Decimal` (vía
`str`, nunca `Decimal(float)`) y a `datetime` UTC, y se calcula el spread bid/ask en %.
"""

import math
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from typing import Final

from app.domain.numeric import DECIMAL_CONTEXT

SPREAD_QUANT: Final = Decimal("0.0001")
"""Cuantización del spread: 4 decimales (AC-8)."""

_HUNDRED: Final = Decimal(100)
_TWO: Final = Decimal(2)
_MS_PER_SECOND: Final = 1000


def to_decimal(value: float | None) -> Decimal | None:
    """`None`, NaN o ±inf → `None`; si no, `Decimal(str(value))` (AC-3, AC-5)."""
    if value is None:
        return None
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return Decimal(str(value))


def epoch_ms_to_utc(value: int | None) -> datetime | None:
    """Epoch en milisegundos → `datetime` con `tzinfo=UTC`; `None` → `None` (AC-4)."""
    if value is None:
        return None
    seconds, millis = divmod(value, _MS_PER_SECOND)
    return datetime.fromtimestamp(seconds, tz=UTC).replace(microsecond=millis * 1000)


def epoch_s_to_utc(value: float) -> datetime:
    """Epoch en segundos (p. ej. `received_at`) → `datetime` UTC (AC-4)."""
    return datetime.fromtimestamp(value, tz=UTC)


def spread_pct(bid: Decimal | None, ask: Decimal | None) -> Decimal | None:
    """Spread entre ask y bid en % sobre el precio medio, con 4 decimales (ROUND_HALF_EVEN).

    `None` si falta alguno o alguno es <= 0 (AC-9). Con libro cruzado (ask < bid) el
    resultado es negativo y no se recorta (AC-10).
    """
    if bid is None or ask is None or bid <= 0 or ask <= 0:
        return None
    with localcontext(DECIMAL_CONTEXT):
        mid = (ask + bid) / _TWO
        raw = (ask - bid) / mid * _HUNDRED
        return raw.quantize(SPREAD_QUANT, rounding=ROUND_HALF_EVEN)
