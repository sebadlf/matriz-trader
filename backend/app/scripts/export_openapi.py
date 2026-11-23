"""Vuelca el esquema OpenAPI a `backend/openapi.json` (input de Orval).

Uso: `uv run python -m app.scripts.export_openapi`. No levanta el servidor ni usa la DB.
"""

import json
from pathlib import Path
from typing import Any, Final

from app.main import create_app

OUTPUT: Final = Path(__file__).resolve().parents[2] / "openapi.json"  # backend/openapi.json


def render_openapi() -> str:
    """Serializa el OpenAPI con formato estable (indent 2, claves ordenadas, newline final)."""
    schema: dict[str, Any] = create_app().openapi()
    return json.dumps(schema, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def main() -> None:
    OUTPUT.write_text(render_openapi(), encoding="utf-8")
    print(f"OpenAPI escrito en {OUTPUT}")


if __name__ == "__main__":
    main()
