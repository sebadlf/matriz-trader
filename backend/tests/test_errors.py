"""Errores RFC 9457: toda respuesta de error es `application/problem+json` (AC-48)."""

import json
from collections.abc import AsyncIterator
from typing import Any, ClassVar

import pytest
from fastapi import FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient, Response

from app.api.errors import PROBLEM_MEDIA_TYPE
from app.domain.errors import DomainError
from app.main import create_app
from app.scripts.export_openapi import OUTPUT

PROBLEM_KEYS = {"type", "title", "status", "detail", "instance", "correlation_id"}


class OrderRejectedError(DomainError):
    status: ClassVar[int] = 409
    title: ClassVar[str] = "Orden rechazada"


def _build_test_app() -> FastAPI:
    """App real más endpoints de prueba que solo existen en este test."""
    app = create_app()

    @app.get("/_test/items/{item_id}")
    async def get_item(item_id: int) -> dict[str, int]:
        return {"item_id": item_id}

    @app.get("/_test/domain")
    async def raise_domain() -> None:
        raise DomainError("La cantidad supera el máximo por orden")

    @app.get("/_test/domain-subclass")
    async def raise_domain_subclass() -> None:
        raise OrderRejectedError("Kill switch activo")

    @app.get("/_test/nonstandard")
    async def raise_nonstandard_status() -> None:
        raise HTTPException(status_code=599, detail={"code": "x"})

    @app.get("/_test/boom")
    async def raise_unhandled() -> None:
        raise RuntimeError("secreto interno")

    return app


@pytest.fixture
async def error_client() -> AsyncIterator[AsyncClient]:
    # `raise_app_exceptions=False`: ServerErrorMiddleware re-lanza tras responder el 500.
    transport = ASGITransport(app=_build_test_app(), raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client


def _assert_problem(response: Response, status: int, path: str) -> dict[str, Any]:
    assert response.status_code == status
    assert response.headers["content-type"] == PROBLEM_MEDIA_TYPE
    body: dict[str, Any] = response.json()
    assert body.keys() >= PROBLEM_KEYS
    assert body["type"] == "about:blank"
    assert body["status"] == status
    assert body["instance"] == path
    return body


async def test_unknown_route_returns_404_problem(error_client: AsyncClient) -> None:
    response = await error_client.get("/api/no-existe")
    body = _assert_problem(response, 404, "/api/no-existe")
    assert body["title"] == "Not Found"
    assert body["detail"] == "Not Found"


async def test_method_not_allowed_keeps_allow_header(error_client: AsyncClient) -> None:
    response = await error_client.post("/api/health")
    _assert_problem(response, 405, "/api/health")
    assert response.headers["allow"] == "GET"


async def test_nonstandard_status_uses_generic_title(error_client: AsyncClient) -> None:
    response = await error_client.get("/_test/nonstandard")
    body = _assert_problem(response, 599, "/_test/nonstandard")
    assert body["title"] == "Error"
    assert body["detail"] is None


async def test_validation_error_returns_422_problem(error_client: AsyncClient) -> None:
    response = await error_client.get("/_test/items/abc")
    body = _assert_problem(response, 422, "/_test/items/abc")
    assert body["title"] == "Validación fallida"
    assert body["detail"] == "El request no cumple el esquema"
    assert body["errors"][0]["loc"] == ["path", "item_id"]
    assert body["errors"][0]["type"] == "int_parsing"


async def test_domain_error_returns_problem(error_client: AsyncClient) -> None:
    response = await error_client.get("/_test/domain")
    body = _assert_problem(response, 422, "/_test/domain")
    assert body["title"] == "Regla de dominio violada"
    assert body["detail"] == "La cantidad supera el máximo por orden"


async def test_domain_error_subclass_uses_its_status_and_title(error_client: AsyncClient) -> None:
    response = await error_client.get("/_test/domain-subclass")
    body = _assert_problem(response, 409, "/_test/domain-subclass")
    assert body["title"] == "Orden rechazada"
    assert body["detail"] == "Kill switch activo"


async def test_unhandled_exception_returns_500_without_traceback(
    error_client: AsyncClient,
) -> None:
    response = await error_client.get("/_test/boom")
    body = _assert_problem(response, 500, "/_test/boom")
    assert body["title"] == "Error interno"
    assert body["detail"] is None
    assert "secreto interno" not in response.text
    assert "Traceback" not in response.text


async def test_unhandled_exception_echoes_correlation_id(error_client: AsyncClient) -> None:
    # CorrelationIdMiddleware (T8) fija el id desde el header; el 500 lo arma ServerErrorMiddleware,
    # por fuera de ese middleware, y debe devolverlo igual en el cuerpo y en el header.
    request_id = "0b8f4a52c3a44e0f9d7f1a2b3c4d5e6f"
    response = await error_client.get("/_test/boom", headers={"X-Request-ID": request_id})
    body = _assert_problem(response, 500, "/_test/boom")
    assert body["correlation_id"] == request_id
    assert response.headers["x-request-id"] == request_id


def test_openapi_declares_problem_details() -> None:
    schema: dict[str, Any] = json.loads(OUTPUT.read_text(encoding="utf-8"))
    assert "ProblemDetails" in schema["components"]["schemas"]
    responses = schema["paths"]["/api/health"]["get"]["responses"]
    for status in ("404", "422", "500"):
        content = responses[status]["content"]
        ref = {"$ref": "#/components/schemas/ProblemDetails"}
        assert content["application/json"]["schema"] == ref
        assert content[PROBLEM_MEDIA_TYPE]["schema"] == ref
