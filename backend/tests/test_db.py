"""Capa de base de datos: base declarativa y fábrica de sesiones (AC-11, AC-16)."""

from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.db.base import NAMING_CONVENTION, Base, TimestampMixin
from app.db.session import build_engine, build_session_factory

TEST_URL = "postgresql+psycopg://u:p@localhost:5432/test"


def test_base_has_no_business_models() -> None:
    assert Base.metadata.tables == {}
    assert dict(Base.metadata.naming_convention) == NAMING_CONVENTION


def test_timestamp_mixin_uses_mapped_annotations() -> None:
    assert TimestampMixin.__annotations__ == {
        "created_at": Mapped[datetime],
        "updated_at": Mapped[datetime],
    }


def test_timestamp_mixin_produces_timezone_aware_columns() -> None:
    class ProbeBase(DeclarativeBase):
        pass

    class Probe(TimestampMixin, ProbeBase):
        __tablename__ = "probe"
        id: Mapped[int] = mapped_column(primary_key=True)

    for name in ("created_at", "updated_at"):
        column = Probe.__table__.c[name]
        assert isinstance(column.type, DateTime)
        assert column.type.timezone is True
        assert column.server_default is not None
    assert Probe.__table__.c["updated_at"].onupdate is not None


async def test_engine_and_session_factory_target_postgres() -> None:
    engine = build_engine(TEST_URL)
    try:
        assert engine.url.drivername == "postgresql+psycopg"
        factory = build_session_factory(engine)
        assert isinstance(factory, async_sessionmaker)
        async with factory() as session:
            assert isinstance(session, AsyncSession)
            assert session.bind is engine
    finally:
        await engine.dispose()
