"""Test de arquitectura: campos monetarios solo como `Decimal` / `Numeric(p, s)` (AC-52)."""

import importlib
import inspect
import pkgutil
import re
import types
from collections.abc import Iterable
from decimal import Decimal
from typing import Annotated, Final, Union, get_args, get_origin

from pydantic import BaseModel
from sqlalchemy import Column, Float, MetaData, Numeric, Table

import app.schemas
from app.db.base import Base

MONEY_FIELD: Final = re.compile(
    r"price|qty|quantity|amount|notional|money|pnl|balance", re.IGNORECASE
)


def schema_models() -> list[type[BaseModel]]:
    """Todas las subclases de `BaseModel` definidas en `app.schemas`."""
    models: list[type[BaseModel]] = []
    for info in pkgutil.walk_packages(app.schemas.__path__, prefix="app.schemas."):
        module = importlib.import_module(info.name)
        models.extend(
            obj
            for _, obj in inspect.getmembers(module, inspect.isclass)
            if issubclass(obj, BaseModel) and obj.__module__ == module.__name__
        )
    return models


def _unwrap_optional(annotation: object) -> object:
    """`T | None` → `T`; además quita un `Annotated[...]` interno (p. ej. `Price | None`)."""
    if get_origin(annotation) in (Union, types.UnionType):
        args = [arg for arg in get_args(annotation) if arg is not type(None)]
        if len(args) == 1:
            annotation = args[0]
    if get_origin(annotation) is Annotated:
        return get_args(annotation)[0]
    return annotation


def schema_violations(models: Iterable[type[BaseModel]]) -> list[str]:
    """`<Modelo>.<campo>: <tipo>` por cada campo monetario que no es `Decimal`."""
    violations: list[str] = []
    for model in models:
        for name, field in model.model_fields.items():
            if not MONEY_FIELD.search(name):
                continue
            annotation = _unwrap_optional(field.annotation)
            if annotation is not Decimal:
                violations.append(f"{model.__name__}.{name}: {annotation!r}")
    return violations


def table_violations(tables: Iterable[Table]) -> list[str]:
    """`<tabla>.<columna>: <tipo>` por cada columna monetaria que no es `Numeric(p, s)` decimal."""
    violations: list[str] = []
    for table in tables:
        for column in table.columns:
            if not MONEY_FIELD.search(column.name):
                continue
            col_type = column.type
            is_valid = (
                isinstance(col_type, Numeric)
                and not isinstance(col_type, Float)
                and col_type.precision is not None
                and col_type.scale is not None
                and col_type.asdecimal
            )
            if not is_valid:
                violations.append(f"{table.name}.{column.name}: {col_type!r}")
    return violations


def test_schemas_use_decimal_for_money_fields() -> None:
    assert schema_violations(schema_models()) == []


def test_orm_uses_numeric_for_money_columns() -> None:
    assert table_violations(Base.metadata.tables.values()) == []


def test_detects_float_field_in_schema() -> None:
    class ProbeOrder(BaseModel):
        price: float
        quantity: Decimal | None = None
        side: str

    assert schema_violations([ProbeOrder]) == ["ProbeOrder.price: <class 'float'>"]


def test_detects_non_numeric_money_columns() -> None:
    probe = Table(
        "probe_fills",
        MetaData(),
        Column("amount", Float),
        Column("notional", Numeric()),
        Column("price", Numeric(20, 8)),
        Column("side", Float),
    )

    violations = table_violations([probe])

    assert len(violations) == 2
    assert violations[0].startswith("probe_fills.amount: Float")
    assert violations[1].startswith("probe_fills.notional: Numeric")
