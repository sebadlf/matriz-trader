"""Tests de configuración y env faltante del worker (AC-18, AC-36)."""

import logging

import pytest
from worker.__main__ import main
from worker.settings import WorkerSettings

MATRIZ_VARS = ("MATRIZ_BASE_URL", "MATRIZ_USERNAME", "MATRIZ_PASSWORD")


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (*MATRIZ_VARS, "WORKER_HEARTBEAT_SECONDS", "LOG_LEVEL"):
        monkeypatch.delenv(name, raising=False)


def test_reads_matriz_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MATRIZ_BASE_URL", "https://matriz.example.invalid")
    monkeypatch.setenv("MATRIZ_USERNAME", "user")
    monkeypatch.setenv("MATRIZ_PASSWORD", "secret")
    monkeypatch.setenv("WORKER_HEARTBEAT_SECONDS", "5")

    settings = WorkerSettings(_env_file=None)  # pyright: ignore[reportCallIssue]

    assert settings.matriz_base_url == "https://matriz.example.invalid"
    assert settings.matriz_username == "user"
    assert settings.matriz_password.get_secret_value() == "secret"
    assert "secret" not in repr(settings)
    assert settings.worker_heartbeat_seconds == 5.0


def test_missing_env_exits_2_naming_vars(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.ERROR):
        assert main(env_file=None) == 2

    assert (
        "Missing required environment variables: "
        "MATRIZ_BASE_URL, MATRIZ_PASSWORD, MATRIZ_USERNAME" in caplog.text
    )


def test_partially_missing_env_names_only_missing(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setenv("MATRIZ_BASE_URL", "https://matriz.example.invalid")
    monkeypatch.setenv("MATRIZ_USERNAME", "user")

    with caplog.at_level(logging.ERROR):
        assert main(env_file=None) == 2

    assert "Missing required environment variables: MATRIZ_PASSWORD" in caplog.text
