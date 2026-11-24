"""Reloj inyectable (AC-54): toda lectura de la hora pasa por acá, siempre en UTC con zona."""

from datetime import UTC, datetime
from typing import Protocol


class Clock(Protocol):
    """Fuente de la hora actual. En tests se reemplaza por un reloj fijo."""

    def now(self) -> datetime:
        """Devuelve la hora actual en UTC, con `tzinfo`."""
        ...


class SystemClock:
    """Reloj real del sistema."""

    def now(self) -> datetime:
        """Hora actual del sistema en UTC."""
        return datetime.now(UTC)


def get_clock() -> Clock:
    """Dependencia de FastAPI; se reemplaza con `app.dependency_overrides[get_clock]`."""
    return SystemClock()
