"""Reloj inyectable `Clock` y su dependencia `ClockDep` (AC-54)."""

from datetime import UTC, datetime

from fastapi import APIRouter, FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.deps import ClockDep
from app.core.clock import Clock, SystemClock, get_clock

FIXED_NOW = datetime(2026, 1, 2, 13, 30, tzinfo=UTC)


class FixedClock:
    """Reloj de prueba que siempre devuelve `FIXED_NOW`."""

    def now(self) -> datetime:
        return FIXED_NOW


def test_system_clock_returns_aware_utc() -> None:
    now = SystemClock().now()
    assert now.tzinfo is UTC
    assert now.utcoffset() is not None


def test_get_clock_returns_system_clock() -> None:
    clock: Clock = get_clock()
    assert isinstance(clock, SystemClock)


def _app_with_clock_route() -> FastAPI:
    router = APIRouter()

    @router.get("/probe-clock")
    async def probe_clock(clock: ClockDep) -> dict[str, str]:
        return {"now": clock.now().isoformat()}

    app = FastAPI()
    app.include_router(router)
    return app


async def test_clock_dep_uses_system_clock_by_default() -> None:
    app = _app_with_clock_route()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/probe-clock")
    assert response.status_code == 200
    assert datetime.fromisoformat(response.json()["now"]).tzinfo is not None


async def test_clock_dep_can_be_overridden() -> None:
    app = _app_with_clock_route()
    app.dependency_overrides[get_clock] = FixedClock
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/probe-clock")
    assert response.status_code == 200
    assert response.json() == {"now": FIXED_NOW.isoformat()}
