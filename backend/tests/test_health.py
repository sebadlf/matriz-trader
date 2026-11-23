"""AC-10: el backend sirve el OpenAPI y `GET /api/health`."""

from httpx import AsyncClient

from app import __version__


async def test_openapi_is_served(client: AsyncClient) -> None:
    response = await client.get("/api/openapi.json")

    assert response.status_code == 200
    assert "/api/health" in response.json()["paths"]


async def test_health_returns_ok(client: AsyncClient) -> None:
    response = await client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "matriz-trader-backend",
        "version": __version__,
    }


async def test_health_operation_id_is_stable(client: AsyncClient) -> None:
    response = await client.get("/api/openapi.json")

    assert response.json()["paths"]["/api/health"]["get"]["operationId"] == "getHealth"
