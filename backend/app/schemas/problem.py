"""Cuerpo de error estándar RFC 9457 (Problem Details for HTTP APIs)."""

from pydantic import BaseModel


class ValidationIssue(BaseModel):
    """Un error de validación del request, tomado de `RequestValidationError.errors()`."""

    loc: list[str | int]
    msg: str
    type: str


class ProblemDetails(BaseModel):
    """Error RFC 9457 que devuelve toda respuesta de error de la API."""

    type: str = "about:blank"
    title: str
    status: int
    detail: str | None = None
    instance: str | None = None
    correlation_id: str | None = None
    errors: list[ValidationIssue] | None = None
