"""Dependencias de FastAPI compartidas por las rutas.

Es la única puerta de `app.api` hacia la base de datos (contrato de import-linter
«API sin acceso directo a la DB»).
"""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock, get_clock
from app.core.config import Settings, get_settings
from app.db.session import get_session
from app.services.market_data import MarketDataSource, open_market_data_client

SessionDep = Annotated[AsyncSession, Depends(get_session)]
ClockDep = Annotated[Clock, Depends(get_clock)]


async def get_market_data_source(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AsyncIterator[MarketDataSource]:
    """Cliente de `market-data-client` nuevo por request, cerrado al terminar el request."""
    async with open_market_data_client(settings) as source:
        yield source


MarketDataSourceDep = Annotated[MarketDataSource, Depends(get_market_data_source)]
