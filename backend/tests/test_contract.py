"""Contrato de la API: Schemathesis contra la app ASGI en proceso (AC-34).

El esquema es el `openapi.json` versionado (el mismo que consume Orval), no el que
expone la app en runtime: así un handler que se desvía del contrato publicado falla
aunque nadie haya regenerado el archivo. `call_and_validate(app=...)` usa el
transporte ASGI, sin servidor, sin `lifespan` y sin base de datos.
"""

from pathlib import Path
from typing import Any, Final

import schemathesis

from app.api.deps import get_market_data_source
from app.main import create_app
from tests.test_market_data_service import FakeSource, make_snapshot

OPENAPI_PATH: Final = Path(__file__).resolve().parents[1] / "openapi.json"
APP: Final = create_app()
# Fuente fija: Schemathesis nunca sale a la red ni a Auth0.
APP.dependency_overrides[get_market_data_source] = lambda: FakeSource([make_snapshot("GGAL")])

schema = schemathesis.openapi.from_path(OPENAPI_PATH)


# `Case` es genérico en la operación; la de OpenAPI no exporta un alias público concreto.
@schema.parametrize()
def test_api_cumple_contrato(case: schemathesis.Case[Any]) -> None:
    case.call_and_validate(app=APP)
