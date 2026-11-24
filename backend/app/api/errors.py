"""Traducción de excepciones a respuestas RFC 9457 (`application/problem+json`)."""

import logging
from collections.abc import Mapping
from http import HTTPStatus
from typing import Any, Final

from asgi_correlation_id import correlation_id
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.domain.errors import DomainError
from app.schemas.problem import ProblemDetails, ValidationIssue

PROBLEM_MEDIA_TYPE: Final = "application/problem+json"
_PROBLEM_CONTENT: Final = {
    PROBLEM_MEDIA_TYPE: {"schema": {"$ref": "#/components/schemas/ProblemDetails"}},
}
# `model` registra el componente y publica application/json (lo que tipa Orval); `content` agrega
# application/problem+json para que Schemathesis acepte el Content-Type real de la respuesta.
PROBLEM_RESPONSES: Final[dict[int | str, dict[str, Any]]] = {
    404: {
        "model": ProblemDetails,
        "content": _PROBLEM_CONTENT,
        "description": "No encontrado (RFC 9457)",
    },
    422: {
        "model": ProblemDetails,
        "content": _PROBLEM_CONTENT,
        "description": "Validación (RFC 9457)",
    },
    500: {
        "model": ProblemDetails,
        "content": _PROBLEM_CONTENT,
        "description": "Error interno (RFC 9457)",
    },
}
# Fallo del servicio de market data (502): lo agrega a su `responses=` cada ruta que lo consulta.
UPSTREAM_PROBLEM_RESPONSE: Final[dict[int | str, dict[str, Any]]] = {
    502: {
        "model": ProblemDetails,
        "content": _PROBLEM_CONTENT,
        "description": "Market data no disponible (RFC 9457)",
    },
}

logger = logging.getLogger(__name__)


def _status_phrase(status: int) -> str:
    try:
        return HTTPStatus(status).phrase
    except ValueError:
        return "Error"


def _problem(
    request: Request,
    *,
    status: int,
    title: str,
    detail: str | None = None,
    errors: list[ValidationIssue] | None = None,
) -> ProblemDetails:
    return ProblemDetails(
        title=title,
        status=status,
        detail=detail,
        instance=request.url.path,
        correlation_id=correlation_id.get(),
        errors=errors,
    )


def _respond(problem: ProblemDetails, headers: Mapping[str, str] | None = None) -> JSONResponse:
    return JSONResponse(
        problem.model_dump(mode="json"),
        status_code=problem.status,
        media_type=PROBLEM_MEDIA_TYPE,
        headers=headers,
    )


async def _http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, str) else None
    problem = _problem(
        request, status=exc.status_code, title=_status_phrase(exc.status_code), detail=detail
    )
    return _respond(problem, exc.headers)


async def _validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    issues = [
        ValidationIssue(loc=list(error["loc"]), msg=error["msg"], type=error["type"])
        for error in exc.errors()
    ]
    problem = _problem(
        request,
        status=422,
        title="Validación fallida",
        detail="El request no cumple el esquema",
        errors=issues,
    )
    return _respond(problem)


async def _domain_exception_handler(request: Request, exc: DomainError) -> JSONResponse:
    return _respond(_problem(request, status=exc.status, title=exc.title, detail=exc.detail))


async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Excepción no manejada en %s", request.url.path, exc_info=exc)
    # Starlette atiende `Exception` en ServerErrorMiddleware, por fuera de CorrelationIdMiddleware:
    # el header de correlación se agrega a mano.
    request_id = correlation_id.get()
    headers = {"X-Request-ID": request_id} if request_id else None
    return _respond(_problem(request, status=500, title="Error interno"), headers)


def register_exception_handlers(app: FastAPI) -> None:
    """Registra los handlers que convierten cada error en un `ProblemDetails`."""
    app.exception_handler(StarletteHTTPException)(_http_exception_handler)
    app.exception_handler(RequestValidationError)(_validation_exception_handler)
    app.exception_handler(DomainError)(_domain_exception_handler)
    app.exception_handler(Exception)(_unhandled_exception_handler)
