"""Unit tests de `model` sin base de datos (AC-19, AC-20, AC-21, AC-36)."""

import pytest
from pydantic import ValidationError
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

import model
from model import Base, DatabaseSettings, create_engine_from_url, get_sessionmaker, missing_env_vars

URL = "postgresql+psycopg://user:secret@localhost:5432/test"


class Example(Base):
    __tablename__ = "example"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)


def test_public_api() -> None:
    assert set(model.__all__) >= {
        "Base",
        "create_engine_from_url",
        "get_engine",
        "get_sessionmaker",
    }


def test_base_is_declarative() -> None:
    assert issubclass(Base, DeclarativeBase)


def test_typed_model_uses_naming_convention() -> None:
    table = Base.metadata.tables["example"]
    assert table.primary_key.name == "pk_example"
    assert {c.name for c in table.constraints} >= {"uq_example_name"}


def test_engine_is_postgresql_without_connecting() -> None:
    engine = create_engine_from_url(URL)
    assert engine.dialect.name == "postgresql"
    assert engine.dialect.driver == "psycopg"


def test_sessionmaker_binds_engine() -> None:
    engine = create_engine_from_url(URL)
    factory = get_sessionmaker(engine)
    with factory() as session:
        assert isinstance(session, Session)
        assert session.get_bind() is engine


def test_database_settings_reads_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", URL)
    assert DatabaseSettings(_env_file=None).database_url == URL  # pyright: ignore[reportCallIssue]


def test_missing_env_vars_lists_names(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError) as exc_info:
        DatabaseSettings(_env_file=None)  # pyright: ignore[reportCallIssue]
    assert missing_env_vars(exc_info.value) == ["DATABASE_URL"]
