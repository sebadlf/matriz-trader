"""`GET /api/health`: estado del servicio, sin tocar la base de datos."""

from fastapi import APIRouter

from app import __version__
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", operation_id="getHealth", tags=["health"], response_model=HealthResponse)
async def get_health() -> HealthResponse:
    """Devuelve el estado del servicio."""
    return HealthResponse(status="ok", service="matriz-trader-backend", version=__version__)
