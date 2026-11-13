"""Endpoint `GET /health` con verificación de PostgreSQL (AC-10, AC-11)."""

import logging
import threading
from collections.abc import Callable
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import BaseModel
from sqlalchemy import URL, Engine, text
from sqlalchemy.exc import DBAPIError, SQLAlchemyError

logger = logging.getLogger(__name__)

router = APIRouter()

DbProbe = Callable[[], bool]

_REDACTED = "***"


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    database: Literal["ok", "unavailable"]


def probe_database(engine: Engine) -> SQLAlchemyError | None:
    """Ejecuta `SELECT 1`; devuelve la excepción capturada o `None` si la base responde."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        return exc
    return None


def ping_database(engine: Engine) -> bool:
    return probe_database(engine) is None


def describe_db_error(exc: SQLAlchemyError, url: URL) -> str:
    """Una línea `<tipo>: <mensaje del driver>` sin contraseña ni URL completa (AC-3)."""
    orig = exc.orig if isinstance(exc, DBAPIError) else None
    if orig is not None:
        # `exc.orig` evita el SQL y el sufijo "Background on this error at: ..." de SQLAlchemy.
        kind = f"{type(orig).__module__}.{type(orig).__qualname__}"
        message = str(orig)
    else:
        kind = type(exc).__qualname__
        message = str(exc)
    message = " ".join(message.split())
    secrets = [url.render_as_string(hide_password=False), url.password]
    for secret in secrets:
        if secret:
            message = message.replace(str(secret), _REDACTED)
    return f"{kind}: {message}"


def _target(url: URL) -> str:
    return f"{url.host}:{url.port or 5432}/{url.database}"


class DatabaseStatusTracker:
    """Sondea la base y loguea solo cuando cambia el estado (por proceso)."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._last_ok: bool | None = None  # None = todavía no se sondeó
        self._lock = threading.Lock()

    def __call__(self) -> bool:
        # Sondeo fuera del lock para no serializar requests; `probe_database` se busca por
        # nombre de módulo para que los tests puedan monkeypatchearla.
        exc = probe_database(self._engine)
        ok = exc is None
        url = self._engine.url
        with self._lock:
            previous = self._last_ok
            self._last_ok = ok
            if exc is not None and previous is not False:
                logger.error(
                    "Database unavailable: %s [target=%s]",
                    describe_db_error(exc, url),
                    _target(url),
                )
            elif ok and previous is False:
                logger.info("Database connection restored [target=%s]", _target(url))
        return ok


def get_db_probe(request: Request) -> DbProbe:
    tracker: DatabaseStatusTracker = request.app.state.db_probe
    return tracker


@router.get(
    "/health",
    operation_id="getHealth",
    tags=["health"],
    response_model=HealthResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": HealthResponse}},
)
def get_health(
    response: Response, probe: Annotated[DbProbe, Depends(get_db_probe)]
) -> HealthResponse:
    if probe():
        return HealthResponse(status="ok", database="ok")
    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthResponse(status="degraded", database="unavailable")
