"""El `frontend/openapi.json` versionado coincide con el esquema actual del backend (AC-6)."""

from backend.export_openapi import DEFAULT_OUTPUT, render_openapi


def test_frontend_openapi_snapshot_is_up_to_date() -> None:
    assert DEFAULT_OUTPUT.read_text(encoding="utf-8") == render_openapi(), (
        "frontend/openapi.json está desactualizado: "
        "corré `uv run python -m backend.export_openapi` y commitealo"
    )
