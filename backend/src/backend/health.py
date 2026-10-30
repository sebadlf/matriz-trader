"""Endpoint `GET /health` con verificación de PostgreSQL (AC-10, AC-11)."""

from collections.abc import Callable
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import BaseModel
from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter()

DbProbe = Callable[[], bool]


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    database: Literal["ok", "unavailable"]


def ping_database(engine: Engine) -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return False
    return True


def get_db_probe(request: Request) -> DbProbe:
    engine: Engine = request.app.state.engine
    return lambda: ping_database(engine)


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
