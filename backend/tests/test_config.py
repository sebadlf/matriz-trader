"""`Settings`: carga, arranque abortado ante configuración inválida y variables de librerías."""

import os
import subprocess
import sys
from pathlib import Path
from typing import Final

import pytest
import structlog
from pydantic import HttpUrl

from app.core.config import (
    MARKET_DATA_BASE_URL_DEFAULT,
    PRIMARY_BASE_URL_DEFAULT,
    ROOT_ENV_FILE,
    Settings,
    load_settings,
)
from app.core.logging import configure_logging
from tests.conftest import TEST_CREDENTIALS, TEST_DATABASE_URL

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


# --- Variables de `matriz-client` y `market-data-client` ---

ENV_EXAMPLE: Final = BACKEND_DIR.parent / ".env.example"
PRIMARY_SECRET: Final = "SENTINEL-primary-9f3a"  # noqa: S105 (centinela ficticio)
MARKET_DATA_SECRET: Final = "SENTINEL-market-data-7c1e"  # noqa: S105 (centinela ficticio)
REQUIRED_CREDENTIALS: Final = tuple(TEST_CREDENTIALS)
URL_VARIABLES: Final = ("PRIMARY_BASE_URL", "MARKET_DATA_BASE_URL", "MARKET_DATA_AUTH0_TOKEN_URL")
MATRIZ_VARIABLES: Final = ("PRIMARY_USER", "PRIMARY_PASSWORD", "PRIMARY_BASE_URL")
MARKET_DATA_VARIABLES: Final = (
    "MARKET_DATA_CLIENT_ID",
    "MARKET_DATA_CLIENT_SECRET",
    "MARKET_DATA_AUDIENCE",
    "MARKET_DATA_AUTH0_TOKEN_URL",
    "MARKET_DATA_BASE_URL",
)
LIBRARY_VARIABLES: Final = MATRIZ_VARIABLES + MARKET_DATA_VARIABLES


@pytest.fixture
def no_env_file(monkeypatch: pytest.MonkeyPatch) -> None:
    """`load_settings()` no lee el `.env` local del desarrollador: solo el entorno del test."""
    monkeypatch.setitem(Settings.model_config, "env_file", None)


@pytest.fixture
def sentinel_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PRIMARY_PASSWORD", PRIMARY_SECRET)
    monkeypatch.setenv("MARKET_DATA_CLIENT_SECRET", MARKET_DATA_SECRET)


def _env_example_lines() -> list[str]:
    return ENV_EXAMPLE.read_text(encoding="utf-8").splitlines()


def _env_example_values() -> dict[str, str]:
    values: dict[str, str] = {}
    for line in _env_example_lines():
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip()
    return values


def _section_variables(header_fragment: str) -> list[str]:
    """Variables definidas entre el encabezado `# --- <fragmento>` y el siguiente encabezado."""
    lines = _env_example_lines()
    start = next(i for i, line in enumerate(lines) if line.startswith(f"# --- {header_fragment}"))
    names: list[str] = []
    for line in lines[start + 1 :]:
        if line.startswith("# ---"):
            break
        if line and not line.startswith("#") and "=" in line:
            names.append(line.partition("=")[0].strip())
    return names


def test_env_example_lists_library_variables_by_section() -> None:
    """AC-1: WHEN se abre `.env.example` THEN hay una sección por librería con sus variables."""
    assert _section_variables("matriz-client") == list(MATRIZ_VARIABLES)
    assert _section_variables("market-data-client") == list(MARKET_DATA_VARIABLES)


@pytest.mark.parametrize("name", LIBRARY_VARIABLES)
def test_env_example_comments_each_library_variable(name: str) -> None:
    """AC-2: WHEN se abre `.env.example` THEN cada variable tiene antes un comentario."""
    lines = _env_example_lines()
    index = next(i for i, line in enumerate(lines) if line.startswith(f"{name}="))
    comment = lines[index - 1]

    assert comment.startswith("# ")
    assert ("Obligatoria" in comment) or ("Opcional" in comment)


@pytest.mark.parametrize(
    ("name", "default"),
    [
        ("PRIMARY_BASE_URL", "https://api.remarkets.primary.com.ar"),
        ("MARKET_DATA_BASE_URL", "https://market-data-develop.bbsa.com.ar/api"),
    ],
)
def test_env_example_comment_states_library_default(name: str, default: str) -> None:
    """AC-2: WHEN la variable tiene default THEN el comentario dice cuál es."""
    lines = _env_example_lines()
    index = next(i for i, line in enumerate(lines) if line.startswith(f"{name}="))

    assert f"default de la librería: {default}" in lines[index - 1]


@pytest.mark.parametrize("name", ["PRIMARY_PASSWORD", "MARKET_DATA_CLIENT_SECRET"])
def test_env_example_secrets_use_non_secret_placeholder(name: str) -> None:
    """AC-3: WHEN se abre `.env.example` THEN los secretos usan un placeholder no secreto."""
    assert _env_example_values()[name] == "change-me-local-only"


def test_env_example_base_urls_match_library_defaults() -> None:
    """AC-4: WHEN se abre `.env.example` THEN las URLs base son los defaults de prueba."""
    values = _env_example_values()

    assert HttpUrl(values["PRIMARY_BASE_URL"]) == PRIMARY_BASE_URL_DEFAULT
    assert HttpUrl(values["MARKET_DATA_BASE_URL"]) == MARKET_DATA_BASE_URL_DEFAULT
    assert PRIMARY_BASE_URL_DEFAULT.host == "api.remarkets.primary.com.ar"
    assert str(MARKET_DATA_BASE_URL_DEFAULT) == "https://market-data-develop.bbsa.com.ar/api"


def test_settings_reads_library_variables_from_env_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-5: WHEN las 8 variables están en el `.env` THEN `Settings` las expone tipadas."""
    for name in LIBRARY_VARIABLES:
        monkeypatch.delenv(name, raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(
        f"DATABASE_URL={TEST_DATABASE_URL}\n"
        "PRIMARY_USER=file-user\n"
        "PRIMARY_PASSWORD=file-primary-password\n"
        "PRIMARY_BASE_URL=https://api.primary.example/\n"
        "MARKET_DATA_CLIENT_ID=file-client-id\n"
        "MARKET_DATA_CLIENT_SECRET=file-market-data-secret\n"
        "MARKET_DATA_AUDIENCE=file-audience\n"
        "MARKET_DATA_AUTH0_TOKEN_URL=https://auth.example/oauth/token\n"
        "MARKET_DATA_BASE_URL=https://md.example/api\n",
        encoding="utf-8",
    )

    settings = Settings(_env_file=env_file)

    assert settings.primary_user == "file-user"
    assert settings.primary_password.get_secret_value() == "file-primary-password"
    assert settings.primary_base_url == HttpUrl("https://api.primary.example/")
    assert settings.market_data_client_id == "file-client-id"
    assert settings.market_data_client_secret.get_secret_value() == "file-market-data-secret"
    assert settings.market_data_audience == "file-audience"
    assert settings.market_data_auth0_token_url == HttpUrl("https://auth.example/oauth/token")
    assert settings.market_data_base_url == HttpUrl("https://md.example/api")


def test_settings_reads_library_variables_from_environment(no_env_file: None) -> None:
    """AC-5: WHEN las variables están en el entorno THEN `Settings` las expone con esos valores."""
    settings = load_settings()

    assert settings.primary_user == TEST_CREDENTIALS["PRIMARY_USER"]
    assert settings.primary_password.get_secret_value() == TEST_CREDENTIALS["PRIMARY_PASSWORD"]
    assert settings.market_data_client_id == TEST_CREDENTIALS["MARKET_DATA_CLIENT_ID"]
    assert (
        settings.market_data_client_secret.get_secret_value()
        == TEST_CREDENTIALS["MARKET_DATA_CLIENT_SECRET"]
    )
    assert settings.market_data_audience == TEST_CREDENTIALS["MARKET_DATA_AUDIENCE"]
    assert settings.market_data_auth0_token_url == HttpUrl(
        TEST_CREDENTIALS["MARKET_DATA_AUTH0_TOKEN_URL"]
    )


def test_base_urls_default_to_library_values(no_env_file: None) -> None:
    """AC-6: WHEN faltan `PRIMARY_BASE_URL` y `MARKET_DATA_BASE_URL` THEN se usan los defaults."""
    settings = load_settings()

    assert settings.primary_base_url == HttpUrl("https://api.remarkets.primary.com.ar")
    assert settings.market_data_base_url == HttpUrl("https://market-data-develop.bbsa.com.ar/api")


@pytest.mark.parametrize("name", URL_VARIABLES)
@pytest.mark.parametrize("value", ["ftp://x.example", "no-scheme.example", "/relativa", ""])
def test_load_settings_exits_when_url_is_invalid(
    name: str,
    value: str,
    no_env_file: None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """AC-7: IF una URL no es `http`/`https` absoluta THEN exit 1 nombrando la variable."""
    monkeypatch.setenv(name, value)

    with pytest.raises(SystemExit) as exc_info:
        load_settings()

    assert exc_info.value.code == 1
    assert name in capsys.readouterr().err


@pytest.mark.parametrize("name", URL_VARIABLES)
def test_app_exits_when_url_is_invalid(name: str) -> None:
    """AC-7: IF una URL es inválida THEN `python -m app` sale con 1 y la nombra en stderr."""
    result = _run_app(**{name: "ftp://x.example"})

    assert result.returncode == 1
    assert name in result.stderr


@pytest.mark.parametrize("name", REQUIRED_CREDENTIALS)
def test_load_settings_exits_when_credential_missing(
    name: str,
    no_env_file: None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """AC-8 (Resolved Decisions 1 y 2): IF falta una credencial THEN exit 1 nombrándola."""
    monkeypatch.delenv(name)

    with pytest.raises(SystemExit) as exc_info:
        load_settings()

    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert f"Configuración inválida: {name}\n" in err


@pytest.mark.parametrize("name", REQUIRED_CREDENTIALS)
@pytest.mark.parametrize("value", ["", "   "])
def test_load_settings_exits_when_credential_is_blank(
    name: str,
    value: str,
    no_env_file: None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """AC-8 (Resolved Decision 5): IF una credencial está vacía THEN exit 1 nombrándola."""
    monkeypatch.setenv(name, value)

    with pytest.raises(SystemExit) as exc_info:
        load_settings()

    assert exc_info.value.code == 1
    assert name in capsys.readouterr().err


def test_load_settings_reports_every_missing_credential_of_a_library(
    no_env_file: None, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-8 (Resolved Decision 2): IF un grupo está incompleto THEN se nombra cada faltante."""
    monkeypatch.delenv("PRIMARY_USER")
    monkeypatch.delenv("PRIMARY_PASSWORD")

    with pytest.raises(SystemExit):
        load_settings()

    assert "Configuración inválida: PRIMARY_USER, PRIMARY_PASSWORD\n" in capsys.readouterr().err


def test_settings_repr_and_str_mask_secrets(no_env_file: None, sentinel_secrets: None) -> None:
    """AC-9: WHEN se obtiene `repr()`/`str()` de `Settings` THEN los secretos están enmascarados."""
    settings = load_settings()

    for text in (repr(settings), str(settings)):
        assert PRIMARY_SECRET not in text
        assert MARKET_DATA_SECRET not in text
        assert "**********" in text


def test_structlog_redacts_settings_secrets(
    no_env_file: None, sentinel_secrets: None, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-9: WHEN se loguea `Settings` con structlog THEN los secretos no aparecen."""
    settings = load_settings()
    configure_logging("production", "info")

    structlog.get_logger("test").info(
        "settings_loaded", settings=settings.model_dump(), settings_repr=repr(settings)
    )

    out = capsys.readouterr().out
    assert "settings_loaded" in out
    assert PRIMARY_SECRET not in out
    assert MARKET_DATA_SECRET not in out
    assert TEST_CREDENTIALS["PRIMARY_USER"] in out


def test_load_settings_stderr_has_no_secrets_on_invalid_url(
    no_env_file: None,
    sentinel_secrets: None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """AC-10: IF `load_settings()` aborta por una URL inválida THEN stderr no tiene secretos."""
    monkeypatch.setenv("PRIMARY_BASE_URL", "ftp://x.example")

    with pytest.raises(SystemExit):
        load_settings()

    err = capsys.readouterr().err
    assert "PRIMARY_BASE_URL" in err
    assert PRIMARY_SECRET not in err
    assert MARKET_DATA_SECRET not in err


def test_load_settings_stderr_has_no_secrets_on_missing_credential(
    no_env_file: None,
    sentinel_secrets: None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """AC-10: IF aborta por una credencial faltante THEN stderr no vuelca la entrada completa."""
    monkeypatch.delenv("PRIMARY_USER")

    with pytest.raises(SystemExit) as exc_info:
        load_settings()

    err = capsys.readouterr().err
    assert "PRIMARY_USER" in err
    assert PRIMARY_SECRET not in err
    assert MARKET_DATA_SECRET not in err
    assert exc_info.value.__cause__ is None
    assert exc_info.value.__suppress_context__


def test_app_stderr_has_no_secrets() -> None:
    """AC-10: IF `python -m app` aborta THEN su stderr (incluido el traceback) no tiene secretos."""
    result = _run_app(
        PRIMARY_PASSWORD=PRIMARY_SECRET,
        MARKET_DATA_CLIENT_SECRET=MARKET_DATA_SECRET,
        MARKET_DATA_AUTH0_TOKEN_URL="no-scheme.example",  # noqa: S106 (es una URL, no un token)
    )

    assert result.returncode == 1
    assert "MARKET_DATA_AUTH0_TOKEN_URL" in result.stderr
    assert PRIMARY_SECRET not in result.stderr
    assert MARKET_DATA_SECRET not in result.stderr
