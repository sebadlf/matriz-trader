"""Dependencias compartidas de la API (`SessionDep`) y ciclo de vida de la app (AC-22)."""

from fastapi import APIRouter, FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.deps import SessionDep
from app.core.config import get_settings
from app.db.session import build_engine, build_session_factory
from app.main import create_app, lifespan
from tests.conftest import TEST_DATABASE_URL


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
