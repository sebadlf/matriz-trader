"""Errores de dominio: reglas de negocio violadas, independientes de HTTP."""

from typing import ClassVar


class DomainError(Exception):
    """Base de los errores de dominio. La API los traduce a RFC 9457 con `status` y `title`."""

    status: ClassVar[int] = 422
    title: ClassVar[str] = "Regla de dominio violada"

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail
