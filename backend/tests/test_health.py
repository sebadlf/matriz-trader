"""Unit tests de `GET /health`, CORS y OpenAPI sin PostgreSQL (AC-10..AC-13, AC-36)."""

import time
from collections.abc import Iterator
from pathlib import Path

import pytest
from backend.export_openapi import main as export_main
from backend.export_openapi import render_openapi
from backend.health import get_db_probe, ping_database
from backend.main import create_app
from backend.settings import BackendSettings
from fastapi import FastAPI
from fastapi.testclient import TestClient

from model import create_engine_from_url

URL = "postgresql+psycopg://user:secret@localhost:5432/test"
DEV_ORIGIN = "http://localhost:5173"


def make_app(probe_result: bool, cors_origins: str = DEV_ORIGIN) -> FastAPI:
    app = create_app(BackendSettings(database_url=URL, cors_origins=cors_origins))
    app.dependency_overrides[get_db_probe] = lambda: lambda: probe_result
    return app


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(make_app(probe_result=True)) as test_client:
        yield test_client


def test_health_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_db_unavailable() -> None:
    with TestClient(make_app(probe_result=False)) as client:
        response = client.get("/health")
    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "database": "unavailable"}


def test_ping_database_fails_fast_when_unreachable() -> None:
    # Puerto cerrado en loopback: no requiere PostgreSQL ni red externa.
    engine = create_engine_from_url("postgresql+psycopg://user:secret@127.0.0.1:1/test")
    started = time.monotonic()
    assert ping_database(engine) is False
    assert time.monotonic() - started < 5


def test_openapi_served(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    operation = schema["paths"]["/health"]["get"]
    assert operation["operationId"] == "getHealth"
    assert set(operation["responses"]) >= {"200", "503"}
    assert "HealthResponse" in schema["components"]["schemas"]


def test_cors_preflight_allows_dev_origin(client: TestClient) -> None:
    response = client.options(
        "/health",
        headers={"Origin": DEV_ORIGIN, "Access-Control-Request-Method": "GET"},
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == DEV_ORIGIN


def test_cors_rejects_unknown_origin(client: TestClient) -> None:
    response = client.get("/health", headers={"Origin": "http://evil.example"})
    assert "access-control-allow-origin" not in response.headers


def test_export_openapi_writes_schema(tmp_path: Path) -> None:
    output = tmp_path / "openapi.json"
    assert export_main([str(output)]) == 0
    assert output.read_text(encoding="utf-8") == render_openapi()
