"""Tabla CFI → tipo de instrumento y regla de división por 100 (AC-1, AC-4, AC-8 a AC-11)."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.domain.utils_instrument import (
    CFI_TO_INSTRUMENT_TYPE,
    InstrumentType,
    classify_cficode,
    should_divide_price_by_100,
)

CFI_TABLE: list[tuple[str, InstrumentType]] = [
    ("ESXXXX", InstrumentType.ACCION),
    ("EMXXXX", InstrumentType.CEDEAR),
    ("DBXXXX", InstrumentType.BONO),
    ("DBXXFR", InstrumentType.OBLIGACION_NEGOCIABLE),
    ("DYXTXR", InstrumentType.LETRA),
    ("FXXXSX", InstrumentType.FUTURO),
    ("OCASPS", InstrumentType.OPCION_SOBRE_ACCION),
    ("OPASPS", InstrumentType.OPCION_SOBRE_ACCION),
    ("OCAFXS", InstrumentType.OPCION_SOBRE_FUTURO),
    ("OPAFXS", InstrumentType.OPCION_SOBRE_FUTURO),
]

DIVIDE_BY_100 = frozenset(
    {
        InstrumentType.BONO,
        InstrumentType.OBLIGACION_NEGOCIABLE,
        InstrumentType.LETRA,
    }
)


@pytest.mark.parametrize(("cficode", "expected"), CFI_TABLE)
def test_classify_cficode_maps_table(cficode: str, expected: InstrumentType) -> None:
    result = classify_cficode(cficode)
    assert result is expected
    assert type(result) is InstrumentType


def test_table_has_exactly_the_documented_codes() -> None:
    assert dict(CFI_TO_INSTRUMENT_TYPE) == dict(CFI_TABLE)


def test_every_member_is_reachable_from_some_cfi() -> None:
    assert set(CFI_TO_INSTRUMENT_TYPE.values()) == set(InstrumentType)


def test_table_is_read_only() -> None:
    with pytest.raises(TypeError):
        CFI_TO_INSTRUMENT_TYPE["XXXXXX"] = InstrumentType.ACCION  # type: ignore[index]


@pytest.mark.parametrize("cficode", [None, "", "LRXXXX", "dbxxxx", " DBXXXX", "DBXXXX "])
def test_classify_cficode_unknown_returns_none(cficode: str | None) -> None:
    assert classify_cficode(cficode) is None


@pytest.mark.parametrize("instrument_type", sorted(DIVIDE_BY_100))
def test_should_divide_true(instrument_type: InstrumentType) -> None:
    assert should_divide_price_by_100(instrument_type) is True


@pytest.mark.parametrize("instrument_type", sorted(set(InstrumentType) - DIVIDE_BY_100))
def test_should_divide_false(instrument_type: InstrumentType) -> None:
    assert should_divide_price_by_100(instrument_type) is False


def test_divide_rule_defined_for_every_member() -> None:
    results = {member: should_divide_price_by_100(member) for member in InstrumentType}
    assert all(isinstance(value, bool) for value in results.values())
    assert {member for member, value in results.items() if value} == DIVIDE_BY_100


def test_divide_rule_by_cfi_code() -> None:
    dividing = {code for code, kind in CFI_TABLE if should_divide_price_by_100(kind)}
    assert dividing == {"DBXXXX", "DBXXFR", "DYXTXR"}


def test_unknown_member_hits_assert_never() -> None:
    with pytest.raises(AssertionError):
        should_divide_price_by_100("NO_EXISTE")  # type: ignore[arg-type]


@given(st.sampled_from(InstrumentType))
def test_should_divide_is_deterministic(instrument_type: InstrumentType) -> None:
    assert should_divide_price_by_100(instrument_type) == should_divide_price_by_100(
        instrument_type
    )
