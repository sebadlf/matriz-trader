"""Unit tests de la configuración del backend (AC-13, AC-46)."""

import logging

import pytest
from backend.settings import DEFAULT_MATRIZ_BASE_URL, BackendSettings, load_settings
from broker.matriz_gateway import MatrizCredentials

URL = "postgresql+psycopg://user:secret@localhost:5432/test"


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch: pytest.MonkeyPatch) -> None:
    # Ignora el `.env` de la raíz para que los tests no dependan del entorno local.
    monkeypatch.setitem(BackendSettings.model_config, "env_file", None)
    for name in (
        "DATABASE_URL",
        "CORS_ORIGINS",
        "LOG_LEVEL",
        "MATRIZ_BASE_URL",
        "MATRIZ_USERNAME",
        "MATRIZ_PASSWORD",
        "MATRIZ_ACCOUNTS",
    ):
        monkeypatch.delenv(name, raising=False)


def test_load_settings_reads_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", URL)
    monkeypatch.setenv("CORS_ORIGINS", " http://localhost:5173 , ,http://127.0.0.1:5173")
    settings = load_settings()
    assert settings.database_url == URL
    assert settings.cors_origin_list == ["http://localhost:5173", "http://127.0.0.1:5173"]


def test_missing_database_url_exits_with_2(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.ERROR), pytest.raises(SystemExit) as exc_info:
        load_settings()
    assert exc_info.value.code == 2
    assert "Missing required environment variables: DATABASE_URL" in caplog.text


def test_matriz_vars_absent_do_not_fail_loading(monkeypatch: pytest.MonkeyPatch) -> None:
    # UB-4: sin `MATRIZ_*` el backend carga igual y no hay credenciales ni cuentas.
    monkeypatch.setenv("DATABASE_URL", URL)
    settings = load_settings()
    assert settings.matriz_base_url == DEFAULT_MATRIZ_BASE_URL
    assert settings.matriz_credentials is None
    assert settings.matriz_account_list == []


def test_matriz_accounts_are_trimmed_and_deduplicated(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", URL)
    monkeypatch.setenv("MATRIZ_ACCOUNTS", " A, ,B,A ")
    assert load_settings().matriz_account_list == ["A", "B"]


def test_matriz_credentials_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", URL)
    monkeypatch.setenv("MATRIZ_BASE_URL", "https://example.test")
    monkeypatch.setenv("MATRIZ_USERNAME", "user")
    monkeypatch.setenv("MATRIZ_PASSWORD", "pw")
    assert load_settings().matriz_credentials == MatrizCredentials(
        base_url="https://example.test", username="user", password="pw"
    )


@pytest.mark.parametrize(("username", "password"), [("user", ""), ("", "pw"), ("  ", "pw")])
def test_matriz_credentials_none_when_incomplete(
    monkeypatch: pytest.MonkeyPatch, username: str, password: str
) -> None:
    monkeypatch.setenv("DATABASE_URL", URL)
    monkeypatch.setenv("MATRIZ_USERNAME", username)
    monkeypatch.setenv("MATRIZ_PASSWORD", password)
    assert load_settings().matriz_credentials is None
