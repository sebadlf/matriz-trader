"""Probe de verify-guards: `datetime.utcnow` devuelve una fecha sin zona horaria (DTZ003)."""

from datetime import datetime


def ahora() -> datetime:
    return datetime.utcnow()
