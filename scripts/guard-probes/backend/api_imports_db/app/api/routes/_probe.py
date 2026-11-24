"""Probe de verify-guards: una ruta no importa modelos de `app.db` (contrato «API sin acceso directo a la DB»)."""

from app.db.base import Base

__all__ = ["Base"]
