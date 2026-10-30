"""Exporta el esquema OpenAPI sin levantar el servidor (AC-6).

Uso: `uv run python -m backend.export_openapi [ruta]` (default: `<repo>/frontend/openapi.json`).
"""

import json
import sys
from pathlib import Path
from typing import Any

from backend.main import create_app
from backend.settings import BackendSettings

DEFAULT_OUTPUT = Path(__file__).resolve().parents[3] / "frontend" / "openapi.json"


def render_openapi() -> str:
    # URL ficticia: crear el engine no conecta.
    settings = BackendSettings(database_url="postgresql+psycopg://export@localhost/export")
    schema: dict[str, Any] = create_app(settings).openapi()
    return json.dumps(schema, indent=2, sort_keys=True) + "\n"


def main(argv: list[str]) -> int:
    output = Path(argv[0]) if argv else DEFAULT_OUTPUT
    output.write_text(render_openapi(), encoding="utf-8")
    print(f"OpenAPI schema written to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
