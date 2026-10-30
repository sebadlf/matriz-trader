"""Aplicación FastAPI (AC-12, AC-13)."""

from functools import cache

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend import health
from backend.settings import BackendSettings, load_settings
from model import create_engine_from_url


def create_app(settings: BackendSettings) -> FastAPI:
    app = FastAPI(title="Matriz Trader API", version="0.1.0")
    # El engine no conecta al crearse: el backend arranca aunque Postgres esté caído.
    app.state.engine = create_engine_from_url(settings.database_url)
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
    return create_app(load_settings())


def __getattr__(name: str) -> FastAPI:
    # `app` se construye al pedirlo (uvicorn `backend.main:app`), no al importar el módulo,
    # para que tests y `export_openapi` no exijan `DATABASE_URL`.
    if name == "app":
        return _default_app()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
