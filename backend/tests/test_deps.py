"""Dependencias compartidas de la API (`SessionDep`) y ciclo de vida de la app (AC-22)."""

import json

import pytest
from fastapi import APIRouter, FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.deps import SessionDep
from app.core.config import get_settings
from app.db.session import build_engine, build_session_factory
from app.main import create_app, lifespan
from tests.conftest import TEST_CREDENTIALS, TEST_DATABASE_URL


async def test_session_dep_opens_one_session_per_request() -> None:
    router = APIRouter()

    @router.get("/probe-session")
    async def probe_session(session: SessionDep) -> dict[str, bool]:
        return {"is_async_session": isinstance(session, AsyncSession)}

    app = FastAPI()
    app.include_router(router)
    engine = build_engine(TEST_DATABASE_URL)  # no abre conexiones: la ruta no ejecuta SQL
    app.state.session_factory = build_session_factory(engine)
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as http_client:
            response = await http_client.get("/probe-session")
    finally:
        await engine.dispose()

    assert response.status_code == 200
    assert response.json() == {"is_async_session": True}


async def test_lifespan_creates_session_factory_from_settings() -> None:
    get_settings.cache_clear()
    app = create_app()
    try:
        async with lifespan(app):
            factory = app.state.session_factory
            assert isinstance(factory, async_sessionmaker)
            assert str(factory.kw["bind"].url) == "postgresql+psycopg://u:***@localhost:5432/test"
    finally:
        get_settings.cache_clear()


async def test_lifespan_logs_external_hosts(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # Valores explícitos: el resultado no depende del `.env` local del desarrollador.
    monkeypatch.setenv("APP_ENV", "production")  # salida JSON
    monkeypatch.setenv("LOG_LEVEL", "info")
    monkeypatch.setenv("PRIMARY_BASE_URL", "https://primary.example.test/api")
    monkeypatch.setenv("MARKET_DATA_BASE_URL", "https://md.example.test/api")
    get_settings.cache_clear()
    app = create_app()
    try:
        async with lifespan(app):
            pass
    finally:
        get_settings.cache_clear()

    out = capsys.readouterr().out
    events = [json.loads(line) for line in out.splitlines() if line.startswith("{")]
    endpoints = [e for e in events if e["event"] == "external_endpoints"]
    assert len(endpoints) == 1
    assert endpoints[0]["primary_host"] == "primary.example.test"
    assert endpoints[0]["market_data_host"] == "md.example.test"
    assert endpoints[0]["market_data_auth_host"] == "auth.test"
    for secret in (
        TEST_CREDENTIALS["PRIMARY_USER"],
        TEST_CREDENTIALS["PRIMARY_PASSWORD"],
        TEST_CREDENTIALS["MARKET_DATA_CLIENT_SECRET"],
        TEST_CREDENTIALS["MARKET_DATA_CLIENT_ID"],
    ):
        assert secret not in out
