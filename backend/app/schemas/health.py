"""Esquemas de respuesta del endpoint de salud."""

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Estado del servicio. No refleja el estado de la base de datos."""

    status: Literal["ok"]
    service: Literal["matriz-trader-backend"]
    version: str
