"""Tests de configuración y env faltante del worker (AC-6, AC-7, AC-18, AC-36)."""

import logging

import pytest
from worker.__main__ import main
from worker.settings import DEFAULT_MARKET_DATA_BASE_URL, WorkerSettings

MATRIZ_VARS = ("MATRIZ_BASE_URL", "MATRIZ_USERNAME", "MATRIZ_PASSWORD")
MARKET_DATA_VARS = (
    "MARKET_DATA_CLIENT_ID",
    "MARKET_DATA_CLIENT_SECRET",
    "MARKET_DATA_AUDIENCE",
    "MARKET_DATA_AUTH0_TOKEN_URL",
    "MARKET_DATA_BASE_URL",
)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (*MATRIZ_VARS, *MARKET_DATA_VARS, "WORKER_HEARTBEAT_SECONDS", "LOG_LEVEL"):
        monkeypatch.delenv(name, raising=False)


def set_matriz_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MATRIZ_BASE_URL", "https://matriz.example.invalid")
    monkeypatch.setenv("MATRIZ_USERNAME", "user")
    monkeypatch.setenv("MATRIZ_PASSWORD", "matriz-pass")


def set_market_data_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MARKET_DATA_CLIENT_ID", "client-id")
    monkeypatch.setenv("MARKET_DATA_CLIENT_SECRET", "md-secret")
    monkeypatch.setenv("MARKET_DATA_AUDIENCE", "audience")
    monkeypatch.setenv("MARKET_DATA_AUTH0_TOKEN_URL", "https://auth.example.invalid/oauth/token")


def test_reads_matriz_env(monkeypatch: pytest.MonkeyPatch) -> None:
    set_matriz_env(monkeypatch)
    set_market_data_env(monkeypatch)
    monkeypatch.setenv("WORKER_HEARTBEAT_SECONDS", "5")

    settings = WorkerSettings(_env_file=None)  # pyright: ignore[reportCallIssue]

    assert settings.matriz_base_url == "https://matriz.example.invalid"
    assert settings.matriz_username == "user"
    assert settings.matriz_password.get_secret_value() == "matriz-pass"
    assert "matriz-pass" not in repr(settings)
    assert settings.worker_heartbeat_seconds == 5.0


def test_reads_market_data_env(monkeypatch: pytest.MonkeyPatch) -> None:
    set_matriz_env(monkeypatch)
    set_market_data_env(monkeypatch)

    settings = WorkerSettings(_env_file=None)  # pyright: ignore[reportCallIssue]

    assert settings.market_data_client_id == "client-id"
    assert settings.market_data_client_secret.get_secret_value() == "md-secret"
    assert "md-secret" not in repr(settings)
    assert settings.market_data_audience == "audience"
    assert settings.market_data_auth0_token_url == "https://auth.example.invalid/oauth/token"
    assert settings.market_data_base_url == DEFAULT_MARKET_DATA_BASE_URL

    monkeypatch.setenv("MARKET_DATA_BASE_URL", "https://md.example.invalid/api")
    settings = WorkerSettings(_env_file=None)  # pyright: ignore[reportCallIssue]
    assert settings.market_data_base_url == "https://md.example.invalid/api"


def test_missing_env_exits_2_naming_vars(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.ERROR):
        assert main(env_file=None) == 2

    assert (
        "Missing required environment variables: "
        "MARKET_DATA_AUDIENCE, MARKET_DATA_AUTH0_TOKEN_URL, MARKET_DATA_CLIENT_ID, "
        "MARKET_DATA_CLIENT_SECRET, MATRIZ_BASE_URL, MATRIZ_PASSWORD, MATRIZ_USERNAME"
        in caplog.text
    )


def test_partially_missing_env_names_only_missing(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    set_market_data_env(monkeypatch)
    monkeypatch.setenv("MATRIZ_BASE_URL", "https://matriz.example.invalid")
    monkeypatch.setenv("MATRIZ_USERNAME", "user")

    with caplog.at_level(logging.ERROR):
        assert main(env_file=None) == 2

    assert "Missing required environment variables: MATRIZ_PASSWORD" in caplog.text


def test_missing_market_data_env_exits_2(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    set_matriz_env(monkeypatch)
    monkeypatch.setenv("MARKET_DATA_CLIENT_ID", "client-id")
    monkeypatch.setenv("MARKET_DATA_AUDIENCE", "audience")

    with caplog.at_level(logging.ERROR):
        assert main(env_file=None) == 2

    assert (
        "Missing required environment variables: "
        "MARKET_DATA_AUTH0_TOKEN_URL, MARKET_DATA_CLIENT_SECRET" in caplog.text
    )
