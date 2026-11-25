"""Tipo de instrumento a partir del código CFI (ISO 10962) y regla de división del precio."""

from enum import StrEnum, unique
from types import MappingProxyType
from typing import Final, assert_never


@unique
class InstrumentType(StrEnum):
    """Nombres estables: renombrar un miembro es un cambio incompatible."""

    ACCION = "ACCION"
    CEDEAR = "CEDEAR"
    BONO = "BONO"
    OBLIGACION_NEGOCIABLE = "OBLIGACION_NEGOCIABLE"
    LETRA = "LETRA"
    FUTURO = "FUTURO"
    OPCION_SOBRE_ACCION = "OPCION_SOBRE_ACCION"
    OPCION_SOBRE_FUTURO = "OPCION_SOBRE_FUTURO"


CFI_TO_INSTRUMENT_TYPE: Final[MappingProxyType[str, InstrumentType]] = MappingProxyType(
    {
        "ESXXXX": InstrumentType.ACCION,
        "EMXXXX": InstrumentType.CEDEAR,
        "DBXXXX": InstrumentType.BONO,
        "DBXXFR": InstrumentType.OBLIGACION_NEGOCIABLE,
        "DYXTXR": InstrumentType.LETRA,
        "FXXXSX": InstrumentType.FUTURO,
        "OCASPS": InstrumentType.OPCION_SOBRE_ACCION,
        "OPASPS": InstrumentType.OPCION_SOBRE_ACCION,
        "OCAFXS": InstrumentType.OPCION_SOBRE_FUTURO,
        "OPAFXS": InstrumentType.OPCION_SOBRE_FUTURO,
    }
)


def classify_cficode(cficode: str | None) -> InstrumentType | None:
    """Igualdad exacta contra la tabla; `None` si el código es `None` o no está (AC-1, AC-5)."""
    if cficode is None:
        return None
    return CFI_TO_INSTRUMENT_TYPE.get(cficode)


def should_divide_price_by_100(instrument_type: InstrumentType) -> bool:
    """`True` para BONO, OBLIGACION_NEGOCIABLE y LETRA; `False` para el resto (AC-8, AC-9).

    `match` sobre cada miembro con `case _: assert_never(instrument_type)`: un miembro
    nuevo sin rama hace fallar mypy strict (AC-11).
    """
    match instrument_type:
        case InstrumentType.BONO | InstrumentType.OBLIGACION_NEGOCIABLE | InstrumentType.LETRA:
            return True
        case (
            InstrumentType.ACCION
            | InstrumentType.CEDEAR
            | InstrumentType.FUTURO
            | InstrumentType.OPCION_SOBRE_ACCION
            | InstrumentType.OPCION_SOBRE_FUTURO
        ):
            return False
        case _:
            assert_never(instrument_type)
