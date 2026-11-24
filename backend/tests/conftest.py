"""Fixtures compartidas de los tests del backend."""

import logging
from collections.abc import AsyncIterator, Iterator

import pytest
import structlog
from httpx import ASGITransport, AsyncClient

from app.main import create_app

TEST_DATABASE_URL = "postgresql+psycopg://u:p@localhost:5432/test"


@pytest.fixture(autouse=True)
def test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Entorno de test válido, con prioridad sobre el `.env` de la raíz."""
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)


@pytest.fixture(autouse=True)
def restore_logging() -> Iterator[None]:
    """`configure_logging` (lo llama el `lifespan`) cambia el root logger: se restaura al final."""
    root = logging.getLogger()
    handlers, level = root.handlers[:], root.level
    yield
    root.handlers = handlers
    root.setLevel(level)
    structlog.reset_defaults()


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """Cliente HTTP contra la app en memoria. `ASGITransport` no corre el lifespan: no hay DB."""
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
