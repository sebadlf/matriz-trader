"""Entorno de Alembic (plantilla async): `Base.metadata` y URL desde la opción o `Settings`."""

import asyncio
from logging.config import fileConfig
from typing import Final

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import load_settings
from app.db.base import Base

config = context.config

# Logging del CLI. `disable_existing_loggers=False` para no silenciar los loggers del proceso
# que invoca a Alembic (tests, app).
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata

# Ninguna migración espera un lock ni corre sin límite (Squawk: require-lock-timeout y
# require-statement-timeout). Se emiten también en modo offline (`upgrade --sql`).
SESSION_TIMEOUTS: Final = ("SET lock_timeout = '5s'", "SET statement_timeout = '60s'")


def database_url() -> str:
    """La opción explícita `sqlalchemy.url` gana (tests); si no, `DATABASE_URL` de `Settings`."""
    return config.get_main_option("sqlalchemy.url") or str(load_settings().database_url)


def run_migrations_offline() -> None:
    """Genera el SQL de las migraciones sin conectarse a la DB (`alembic upgrade --sql`)."""
    context.configure(
        url=database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        for statement in SESSION_TIMEOUTS:
            context.execute(statement)
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Corre las migraciones sobre una conexión sincrónica (adaptada desde la async)."""
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        for statement in SESSION_TIMEOUTS:
            context.execute(statement)
        context.run_migrations()


async def run_async_migrations() -> None:
    """Crea un engine async sin pool y corre las migraciones en una conexión."""
    connectable = create_async_engine(database_url(), poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Corre las migraciones contra la DB."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
