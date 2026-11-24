"""Fixtures compartidas de los tests del backend."""

import logging
from collections.abc import AsyncIterator, Iterator
from typing import Final

import pytest
import structlog
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.main import create_app

TEST_DATABASE_URL = "postgresql+psycopg://u:p@localhost:5432/test"

# Credenciales ficticias de `matriz-client` y `market-data-client` (obligatorias en `Settings`).
TEST_CREDENTIALS: Final = {
    "PRIMARY_USER": "test-user",
    "PRIMARY_PASSWORD": "test-primary-password",
    "MARKET_DATA_CLIENT_ID": "test-client-id",
    "MARKET_DATA_CLIENT_SECRET": "test-market-data-secret",
    "MARKET_DATA_AUDIENCE": "test-audience",
    "MARKET_DATA_AUTH0_TOKEN_URL": "https://auth.test/oauth/token",
}


@pytest.fixture(autouse=True)
def test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Entorno de test válido, con prioridad sobre el `.env` de la raíz.

    `market_data_client` y `matriz_client` llaman a `load_dotenv()` al importarse y copian
    el `.env` de la raíz a `os.environ`: se borra toda variable de `Settings` para que ni ese
    `.env` ni el shell del desarrollador cambien los defaults ni lo que leen los tests.
    """
    for field in Settings.model_fields:
        monkeypatch.delenv(field.upper(), raising=False)
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    for name, value in TEST_CREDENTIALS.items():
        monkeypatch.setenv(name, value)


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
