"""Tipos numéricos del dominio: precios, cantidades y montos como `Decimal` (AC-51).

Nunca `float`: en JSON viajan como string para no perder precisión en el cliente.
"""

from decimal import ROUND_HALF_EVEN, Context, Decimal
from typing import Annotated, Final

from pydantic import Field, PlainSerializer

DECIMAL_CONTEXT: Final = Context(prec=28, rounding=ROUND_HALF_EVEN)
"""Contexto decimal del dominio: 28 dígitos de precisión y redondeo bancario explícito."""

_as_str: Final = PlainSerializer(str, return_type=str, when_used="json")

Price = Annotated[Decimal, Field(ge=0, max_digits=20, decimal_places=8), _as_str]
Quantity = Annotated[Decimal, Field(ge=0, max_digits=20, decimal_places=8), _as_str]
Money = Annotated[Decimal, Field(max_digits=24, decimal_places=8), _as_str]

MarketDecimal = Annotated[Decimal, Field(allow_inf_nan=False), _as_str]
"""Valor numérico que viene de una fuente externa (precio, tamaño, volumen).

Sin `ge=0` ni `max_digits`: un precio negativo (spreads, calendarios) o con más decimales
no debe convertir la respuesta entera en un 500.
"""
Percent = Annotated[Decimal, Field(allow_inf_nan=False, decimal_places=4), _as_str]
"""Porcentaje con hasta 4 decimales; admite negativos (p. ej. spread con libro cruzado)."""


def round_to_tick(price: Decimal, tick: Decimal) -> Decimal:
    """Redondea `price` al múltiplo de `tick` más cercano (ROUND_HALF_EVEN).

    Lanza `ValueError` si `tick` <= 0.
    """
    if tick <= 0:
        raise ValueError(f"tick debe ser > 0, recibido {tick}")
    steps = (price / tick).quantize(Decimal(1), rounding=ROUND_HALF_EVEN, context=DECIMAL_CONTEXT)
    return (steps * tick).quantize(tick, context=DECIMAL_CONTEXT)
