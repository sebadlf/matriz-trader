"""Esquemas de respuesta de la market data de los instrumentos suscriptos."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.numeric import MarketDecimal, Percent


class MarketDataRow(BaseModel):
    """Último snapshot de un instrumento. Un campo sin dato del servicio es `null`, nunca `"0"`."""

    symbol: str
    market_id: str | None
    bid_price: MarketDecimal | None = Field(description="Precio del mejor bid (BI[0]).")
    bid_size: MarketDecimal | None = Field(description="Cantidad del mejor bid (BI[0]).")
    ask_price: MarketDecimal | None = Field(description="Precio del mejor ask (OF[0]).")
    ask_size: MarketDecimal | None = Field(description="Cantidad del mejor ask (OF[0]).")
    last_price: MarketDecimal | None = Field(description="Precio del último operado (LA).")
    last_size: MarketDecimal | None = Field(description="Cantidad del último operado (LA).")
    last_at: datetime | None = Field(description="Fecha del último operado (LA), en UTC.")
    open_price: MarketDecimal | None = Field(description="Apertura (OP).")
    high_price: MarketDecimal | None = Field(description="Máximo (HI).")
    low_price: MarketDecimal | None = Field(description="Mínimo (LO).")
    close_price: MarketDecimal | None = Field(description="Cierre anterior (CL).")
    settlement_price: MarketDecimal | None = Field(description="Settlement (SE).")
    open_interest: MarketDecimal | None = Field(description="Interés abierto (OI).")
    volume: MarketDecimal | None = Field(description="Volumen operado (TV).")
    spread_pct: Percent | None = Field(
        description="(ask - bid) / precio medio * 100, con 4 decimales; `null` sin bid/ask > 0."
    )
    staleness_seconds: MarketDecimal | None = Field(
        description="Antigüedad del dato según el servicio de market data, en segundos."
    )
    received_at: datetime = Field(description="Momento en que se obtuvo el snapshot, en UTC.")


class MarketDataResponse(BaseModel):
    """Market data de todos los instrumentos suscriptos, ordenada por `symbol` y `market_id`."""

    items: list[MarketDataRow]
    fetched_at: datetime = Field(description="Momento en que se terminó de obtener la lista (UTC).")
