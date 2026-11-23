"""Fábrica de la aplicación FastAPI.

`create_app()` no lee Settings: importar este módulo (tests, export del OpenAPI) no requiere
`.env` ni base de datos. La configuración se carga en el `lifespan`.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import __version__
from app.api.router import api_router
from app.core.config import get_settings
from app.db.session import build_engine, build_session_factory


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Crea el engine y la fábrica de sesiones al arrancar y libera el pool al cerrar."""
    settings = get_settings()
    engine = build_engine(str(settings.database_url))
    app.state.session_factory = build_session_factory(engine)
    try:
        yield
    finally:
        await engine.dispose()


def create_app() -> FastAPI:
    """Construye la aplicación con el OpenAPI en `/api/openapi.json`."""
    app = FastAPI(
        title="matriz-trader API",
        version=__version__,
        lifespan=lifespan,
        openapi_url="/api/openapi.json",
        docs_url="/api/docs",
        redoc_url=None,
    )
    app.include_router(api_router)
    return app


app = create_app()
