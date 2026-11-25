"""Errores de dominio: reglas de negocio violadas, independientes de HTTP."""

from typing import ClassVar


class DomainError(Exception):
    """Base de los errores de dominio. La API los traduce a RFC 9457 con `status` y `title`."""

    status: ClassVar[int] = 422
    title: ClassVar[str] = "Regla de dominio violada"

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class MarketDataUnavailableError(DomainError):
    """El servicio de market data no respondió o respondió con error (se expone como 502)."""

    status: ClassVar[int] = 502
    title: ClassVar[str] = "Market data no disponible"


class InstrumentNotFoundError(DomainError):
    """Matriz no devolvió un instrumento con ese `symbol` y `market_id` (AC-6)."""

    status: ClassVar[int] = 404
    title: ClassVar[str] = "Instrumento no encontrado"


class UnclassifiedInstrumentError(DomainError):
    """El instrumento existe pero su `cficode` es `None` o no está en la tabla (AC-5)."""

    status: ClassVar[int] = 422
    title: ClassVar[str] = "Tipo de instrumento desconocido"
