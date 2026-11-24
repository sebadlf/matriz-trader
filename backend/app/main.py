"""Fábrica de la aplicación FastAPI.

`create_app()` no lee Settings: importar este módulo (tests, export del OpenAPI) no requiere
`.env` ni base de datos. La configuración se carga en el `lifespan`.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI

from app import __version__
from app.api.errors import register_exception_handlers
from app.api.middleware import AccessLogMiddleware
from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import build_engine, build_session_factory


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Crea el engine y la fábrica de sesiones al arrancar y libera el pool al cerrar."""
    settings = get_settings()
    configure_logging(settings.app_env, settings.log_level)
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
    # El último add_middleware es el más externo: CorrelationId envuelve a AccessLog, así el log
    # de acceso ya tiene el id. Un `X-Request-ID` entrante se reutiliza si es un UUID4 válido.
    app.add_middleware(AccessLogMiddleware)
    app.add_middleware(CorrelationIdMiddleware, header_name="X-Request-ID")
    register_exception_handlers(app)
    return app


app = create_app()
