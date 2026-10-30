"""Factories de engine y sesión sobre PostgreSQL (AC-19, AC-21)."""

from functools import cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from model.config import DatabaseSettings


def create_engine_from_url(url: str) -> Engine:
    """Crea el engine sin conectar; los timeouts acotan la espera si Postgres no responde."""
    return create_engine(
        url,
        pool_pre_ping=True,
        pool_timeout=2,
        connect_args={"connect_timeout": 3},
    )


@cache
def get_engine() -> Engine:
    """Engine singleton construido con `DATABASE_URL`."""
    return create_engine_from_url(DatabaseSettings().database_url)  # pyright: ignore[reportCallIssue]


def get_sessionmaker(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)
