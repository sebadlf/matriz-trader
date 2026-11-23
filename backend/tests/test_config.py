"""AC-8 y AC-9: carga de Settings y arranque abortado ante configuración inválida."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from app.core.config import ROOT_ENV_FILE, Settings, load_settings

BACKEND_DIR = Path(__file__).resolve().parents[1]


def _run_app(**overrides: str) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, **overrides}
    return subprocess.run(
        [sys.executable, "-m", "app"],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def test_root_env_file_points_to_repo_root() -> None:
    assert BACKEND_DIR.parent / ".env" == ROOT_ENV_FILE


def test_settings_load_from_env_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DATABASE_URL=postgresql+psycopg://a:b@db:5432/x\nBACKEND_PORT=9000\nLOG_LEVEL=debug\n",
        encoding="utf-8",
    )

    settings = Settings(_env_file=env_file)

    assert str(settings.database_url) == "postgresql+psycopg://a:b@db:5432/x"
    assert settings.backend_port == 9000
    assert settings.log_level == "debug"


def test_load_settings_exits_naming_variable(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("BACKEND_PORT", "abc")

    with pytest.raises(SystemExit) as exc_info:
        load_settings()

    assert exc_info.value.code == 1
    assert "BACKEND_PORT" in capsys.readouterr().err


def test_app_exits_when_database_url_is_invalid() -> None:
    result = _run_app(DATABASE_URL="")

    assert result.returncode == 1
    assert "DATABASE_URL" in result.stderr


def test_app_exits_when_backend_port_is_invalid() -> None:
    result = _run_app(BACKEND_PORT="abc")

    assert result.returncode == 1
    assert "BACKEND_PORT" in result.stderr
