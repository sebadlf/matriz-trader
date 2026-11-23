"""Detecta drift entre `backend/openapi.json` versionado y `app.openapi()`."""

import json

from app.main import create_app
from app.scripts.export_openapi import OUTPUT, render_openapi


def test_openapi_json_matches_app() -> None:
    assert OUTPUT.is_file(), (
        "Falta openapi.json: ejecutá `uv run python -m app.scripts.export_openapi`"
    )
    assert json.loads(OUTPUT.read_text(encoding="utf-8")) == create_app().openapi(), (
        "openapi.json desactualizado: ejecutá `uv run python -m app.scripts.export_openapi`"
    )


def test_openapi_json_is_formatted_like_export() -> None:
    assert OUTPUT.read_text(encoding="utf-8") == render_openapi()
