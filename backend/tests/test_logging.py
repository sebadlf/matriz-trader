"""Observabilidad: `X-Request-ID`, logs con `correlation_id` y redacción de secretos."""

import json
import logging
import uuid
from typing import Any

import pytest
import structlog
from httpx import AsyncClient
from pydantic import SecretStr

from app.core.logging import REDACTED, configure_logging, redact_sensitive


def _json_lines(out: str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in out.splitlines() if line.startswith("{")]


def _is_uuid4_hex(value: str) -> bool:
    try:
        return uuid.UUID(value).version == 4
    except ValueError:
        return False


async def test_response_has_generated_request_id(client: AsyncClient) -> None:
    response = await client.get("/api/health")

    assert _is_uuid4_hex(response.headers["X-Request-ID"])


async def test_valid_incoming_request_id_is_reused(client: AsyncClient) -> None:
    incoming = str(uuid.uuid4())

    response = await client.get("/api/health", headers={"X-Request-ID": incoming})

    assert response.headers["X-Request-ID"] == incoming


async def test_invalid_incoming_request_id_is_replaced(client: AsyncClient) -> None:
    response = await client.get("/api/health", headers={"X-Request-ID": "no-es-un-uuid"})

    request_id = response.headers["X-Request-ID"]
    assert request_id != "no-es-un-uuid"
    assert _is_uuid4_hex(request_id)


async def test_access_log_is_json_with_correlation_id(
    client: AsyncClient, capsys: pytest.CaptureFixture[str]
) -> None:
    configure_logging("production", "info")
    incoming = str(uuid.uuid4())

    await client.get("/api/health", headers={"X-Request-ID": incoming})

    access = [e for e in _json_lines(capsys.readouterr().out) if e["event"] == "request"]
    assert len(access) == 1
    entry = access[0]
    assert entry["correlation_id"] == incoming
    assert entry["method"] == "GET"
    assert entry["path"] == "/api/health"
    assert entry["status"] == 200
    assert entry["level"] == "info"
    assert isinstance(entry["duration_ms"], float)


async def test_access_log_on_404_keeps_status(
    client: AsyncClient, capsys: pytest.CaptureFixture[str]
) -> None:
    configure_logging("production", "info")

    response = await client.get("/api/no-existe")

    access = [e for e in _json_lines(capsys.readouterr().out) if e["event"] == "request"]
    assert access[0]["status"] == 404
    assert access[0]["correlation_id"] == response.headers["X-Request-ID"]


def test_secrets_are_redacted_in_json_output(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging("production", "info")

    structlog.stdlib.get_logger("test").info(
        "login",
        user="ana",
        password="hunter2-plano",  # noqa: S106 - valor falso para probar la redacción
        api_key="clave-plana",
        credentials=SecretStr("secreto-plano"),
        nested={"Access_Token": "token-plano", "ok": "visible"},
    )

    out = capsys.readouterr().out
    entry = _json_lines(out)[0]
    assert entry["user"] == "ana"
    assert entry["password"] == REDACTED
    assert entry["api_key"] == REDACTED
    assert entry["credentials"] == REDACTED
    assert entry["nested"] == {"Access_Token": REDACTED, "ok": "visible"}
    for plain in ("hunter2-plano", "clave-plana", "secreto-plano", "token-plano"):
        assert plain not in out


def test_redact_sensitive_handles_sequences() -> None:
    event = {"event": "x", "items": [{"secret": "s"}, SecretStr("t"), "libre"], "pair": ("a", 1)}

    result = redact_sensitive(None, "info", event)

    assert result["items"] == [{"secret": REDACTED}, REDACTED, "libre"]
    assert result["pair"] == ("a", 1)


def test_stdlib_logs_share_the_json_pipeline(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging("production", "warning")

    logging.getLogger("uvicorn.error").warning("arranque")
    logging.getLogger("uvicorn.error").info("filtrado por nivel")

    entries = _json_lines(capsys.readouterr().out)
    assert [e["event"] for e in entries] == ["arranque"]
    assert entries[0]["logger"] == "uvicorn.error"
    assert entries[0]["level"] == "warning"


def test_development_uses_console_renderer(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging("development", "debug")

    structlog.stdlib.get_logger("test").debug(
        "hola consola",
        token="tk-plano",  # noqa: S106 - valor falso para probar la redacción
    )

    out = capsys.readouterr().out
    assert "hola consola" in out
    assert not out.lstrip().startswith("{")
    assert "tk-plano" not in out
