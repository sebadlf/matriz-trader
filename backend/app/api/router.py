"""Router raíz de la API, montado bajo `/api`."""

from fastapi import APIRouter

from app.api.errors import PROBLEM_RESPONSES
from app.api.routes import health

api_router = APIRouter(prefix="/api", responses=PROBLEM_RESPONSES)
api_router.include_router(health.router)
