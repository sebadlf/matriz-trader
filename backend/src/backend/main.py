"""Aplicación FastAPI (AC-12, AC-13)."""

import logging
import sys
from functools import cache
from typing import TextIO

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend import health
from backend.settings import BackendSettings, load_settings
from model import create_engine_from_url


class _BackendHandler(logging.StreamHandler[TextIO]):
    """Handler propio del logger `backend`; el tipo sirve de marca de idempotencia."""


def configure_logging(level: str) -> None:
    """Hace visibles los logs de `backend.*` bajo uvicorn según `LOG_LEVEL`."""
    backend_logger = logging.getLogger("backend")
    resolved = logging.getLevelNamesMapping().get(level.strip().upper(), logging.INFO)
    backend_logger.setLevel(resolved)
    if not any(isinstance(h, _BackendHandler) for h in backend_logger.handlers):
        handler = _BackendHandler(sys.stderr)  # stderr → `docker compose logs backend`
        handler.setFormatter(logging.Formatter("%(levelname)s:     %(name)s - %(message)s"))
        backend_logger.addHandler(handler)


def create_app(settings: BackendSettings) -> FastAPI:
    app = FastAPI(title="Matriz Trader API", version="0.1.0")
    # El engine no conecta al crearse: el backend arranca aunque Postgres esté caído.
    app.state.engine = create_engine_from_url(settings.database_url)
    app.state.db_probe = health.DatabaseStatusTracker(app.state.engine)
    if settings.cors_origin_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origin_list,
            allow_methods=["GET"],
            allow_headers=["*"],
        )
    app.include_router(health.router)
    return app


@cache
def _default_app() -> FastAPI:
    settings = load_settings()
    configure_logging(settings.log_level)
    return create_app(settings)


def __getattr__(name: str) -> FastAPI:
    # `app` se construye al pedirlo (uvicorn `backend.main:app`), no al importar el módulo,
    # para que tests y `export_openapi` no exijan `DATABASE_URL`.
    if name == "app":
        return _default_app()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
