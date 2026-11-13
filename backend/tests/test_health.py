"""Unit tests de `GET /health`, CORS y OpenAPI sin PostgreSQL (AC-10..AC-13, AC-36)."""

import logging
import time
from collections.abc import Iterator
from pathlib import Path

import pytest
from backend.export_openapi import main as export_main
from backend.export_openapi import render_openapi
from backend.health import describe_db_error, get_db_probe, ping_database
from backend.main import configure_logging, create_app
from backend.settings import BackendSettings
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine, make_url
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from backend import health
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


SENTINEL_PASSWORD = "s3cr3t!pw"
SENTINEL_URL = f"postgresql+psycopg://matriz:{SENTINEL_PASSWORD}@postgres:5432/matriz_trader"


class FakeDriverError(Exception):
    """Simula la excepción del driver (p. ej. `psycopg.OperationalError`)."""


def make_db_error(message: str) -> SQLAlchemyError:
    return OperationalError("SELECT 1", {}, FakeDriverError(message))


def make_tracker(
    monkeypatch: pytest.MonkeyPatch, results: list[SQLAlchemyError | None]
) -> health.DatabaseStatusTracker:
    pending = iter(results)

    def fake_probe(engine: Engine) -> SQLAlchemyError | None:
        return next(pending)

    monkeypatch.setattr(health, "probe_database", fake_probe)
    return health.DatabaseStatusTracker(create_engine_from_url(SENTINEL_URL))


def health_records(caplog: pytest.LogCaptureFixture, level: int) -> list[logging.LogRecord]:
    return [r for r in caplog.records if r.name == "backend.health" and r.levelno == level]


AUTH_ERROR = 'FATAL:  password authentication failed for user "matriz"'


def test_tracker_logs_error_on_first_failure(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    tracker = make_tracker(monkeypatch, [make_db_error(AUTH_ERROR)])
    with caplog.at_level(logging.DEBUG, logger="backend"):
        assert tracker() is False
    errors = health_records(caplog, logging.ERROR)
    assert len(errors) == 1
    message = errors[0].getMessage()
    assert message.startswith("Database unavailable: ")
    assert "FakeDriverError" in message
    assert 'password authentication failed for user "matriz"' in message
    assert "[target=postgres:5432/matriz_trader]" in message
    assert SENTINEL_PASSWORD not in message


def test_tracker_logs_error_once_while_unavailable(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    tracker = make_tracker(
        monkeypatch, [make_db_error(AUTH_ERROR), make_db_error(AUTH_ERROR), make_db_error("x")]
    )
    with caplog.at_level(logging.DEBUG, logger="backend"):
        assert [tracker(), tracker(), tracker()] == [False, False, False]
    assert len(health_records(caplog, logging.ERROR)) == 1
    assert health_records(caplog, logging.INFO) == []


def test_tracker_logs_info_on_recovery(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    tracker = make_tracker(monkeypatch, [None, make_db_error(AUTH_ERROR), None, None])
    with caplog.at_level(logging.DEBUG, logger="backend"):
        assert [tracker(), tracker(), tracker(), tracker()] == [True, False, True, True]
    assert len(health_records(caplog, logging.ERROR)) == 1
    infos = health_records(caplog, logging.INFO)
    assert [r.getMessage() for r in infos] == [
        "Database connection restored [target=postgres:5432/matriz_trader]"
    ]


def test_tracker_silent_on_first_success(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    tracker = make_tracker(monkeypatch, [None, None])
    with caplog.at_level(logging.DEBUG, logger="backend"):
        assert tracker() is True
        assert tracker() is True
    assert [r for r in caplog.records if r.name.startswith("backend")] == []


def test_tracker_real_failure_does_not_leak_password(caplog: pytest.LogCaptureFixture) -> None:
    # Puerto cerrado en loopback: ejercita el driver real sin PostgreSQL.
    url = f"postgresql+psycopg://matriz:{SENTINEL_PASSWORD}@127.0.0.1:1/test"
    tracker = health.DatabaseStatusTracker(create_engine_from_url(url))
    with caplog.at_level(logging.DEBUG, logger="backend"):
        assert tracker() is False
    errors = health_records(caplog, logging.ERROR)
    assert len(errors) == 1
    assert SENTINEL_PASSWORD not in errors[0].getMessage()
    assert "postgresql+psycopg://" not in errors[0].getMessage()


def test_describe_db_error_redacts_password() -> None:
    url = make_url(SENTINEL_URL)
    rendered = url.render_as_string(hide_password=False)  # forma en que SQLAlchemy la imprime
    exc = make_db_error(
        f"connection failed:\n  password {SENTINEL_PASSWORD} rejected\n  url {rendered}"
    )
    described = describe_db_error(exc, url)
    assert described.startswith(f"{__name__}.FakeDriverError: connection failed: ")
    assert "\n" not in described
    assert SENTINEL_PASSWORD not in described
    assert "postgresql+psycopg://" not in described
    assert described.endswith("password *** rejected url ***")


def test_describe_db_error_redacts_password_in_raw_url() -> None:
    # La URL cruda (sin percent-encoding del `!`) no coincide con `render_as_string`,
    # pero la contraseña igual se redacta (AC-3).
    described = describe_db_error(make_db_error(f"url {SENTINEL_URL}"), make_url(SENTINEL_URL))
    assert SENTINEL_PASSWORD not in described


@pytest.fixture
def restore_backend_logger() -> Iterator[logging.Logger]:
    logger = logging.getLogger("backend")
    handlers, level = list(logger.handlers), logger.level
    yield logger
    logger.handlers[:] = handlers
    logger.setLevel(level)


def test_configure_logging_is_idempotent(restore_backend_logger: logging.Logger) -> None:
    logger = restore_backend_logger
    before = len(logger.handlers)
    configure_logging("debug")
    configure_logging("DEBUG")
    assert len(logger.handlers) == before + 1
    assert logger.level == logging.DEBUG
    assert logger.propagate is True


def test_configure_logging_invalid_level_falls_back_to_info(
    restore_backend_logger: logging.Logger,
) -> None:
    configure_logging("nope")
    assert restore_backend_logger.level == logging.INFO


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
