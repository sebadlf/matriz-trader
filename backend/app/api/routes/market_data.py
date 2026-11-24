"""`GET /api/market-data`: último snapshot de todos los instrumentos suscriptos."""

from fastapi import APIRouter

from app.api.deps import ClockDep, MarketDataSourceDep
from app.api.errors import UPSTREAM_PROBLEM_RESPONSE
from app.schemas.market_data import MarketDataResponse
from app.services.market_data import list_market_data

router = APIRouter()


@router.get(
    "/market-data",
    operation_id="listMarketData",
    tags=["market-data"],
    responses=UPSTREAM_PROBLEM_RESPONSE,
)
async def list_market_data_route(
    source: MarketDataSourceDep, clock: ClockDep
) -> MarketDataResponse:
    """Market data de todos los instrumentos suscriptos, con el spread bid/ask en %.

    Responde 502 si el servicio de market data falla, sin datos parciales.
    """
    return await list_market_data(source, clock)
