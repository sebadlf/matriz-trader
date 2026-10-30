"""Unit tests de la configuración del backend (AC-13, AC-46)."""

import logging

import pytest
from backend.settings import BackendSettings, load_settings

URL = "postgresql+psycopg://user:secret@localhost:5432/test"


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch: pytest.MonkeyPatch) -> None:
    # Ignora el `.env` de la raíz para que los tests no dependan del entorno local.
    monkeypatch.setitem(BackendSettings.model_config, "env_file", None)
    for name in ("DATABASE_URL", "CORS_ORIGINS", "LOG_LEVEL"):
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
