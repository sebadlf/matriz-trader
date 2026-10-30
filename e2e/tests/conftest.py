import os
from pathlib import Path

import pytest

DEFAULT_BASE_URL = "http://localhost:8080"


def _env_file_value(name: str) -> str | None:
    """Valor de `name` en el primer `.env` encontrado subiendo desde este archivo."""
    for directory in Path(__file__).resolve().parents:
        candidate = directory / ".env"
        if candidate.is_file():
            for line in candidate.read_text().splitlines():
                key, sep, value = line.partition("=")
                if sep and key.strip() == name:
                    return value.strip().strip("\"'") or None
            return None
    return None


@pytest.fixture(scope="session")
def base_url() -> str:
    """URL base del frontend: `E2E_BASE_URL` del entorno, luego del `.env` raíz (AC-38)."""
    url = os.environ.get("E2E_BASE_URL") or _env_file_value("E2E_BASE_URL") or DEFAULT_BASE_URL
    return url.rstrip("/")
