"""Loop long-running del worker con apagado ordenado por señales (AC-13, AC-14, AC-15, AC-17)."""

import asyncio
import logging
import signal
from collections.abc import Callable

from broker.matriz_gateway import GatewayError, MatrizGateway

from worker.market_data_gateway import MarketDataGateway, MarketDataGatewayError
from worker.settings import WorkerSettings

logger = logging.getLogger(__name__)

CLOSE_TIMEOUT_SECONDS = 5.0
STOP_SIGNALS = (signal.SIGINT, signal.SIGTERM)


async def _close(name: str, close: Callable[[], None]) -> None:
    try:
        await asyncio.wait_for(asyncio.to_thread(close), CLOSE_TIMEOUT_SECONDS)
    except Exception:
        logger.exception("%s close failed", name)


async def _close_all(gateway: MatrizGateway, market_data: MarketDataGateway) -> None:
    await _close("market-data-client", market_data.close)
    await _close("matriz-client", gateway.close)


async def run(
    gateway: MatrizGateway,
    market_data: MarketDataGateway,
    settings: WorkerSettings,
    stop: asyncio.Event,
) -> int:
    try:
        await asyncio.to_thread(gateway.connect)
    except GatewayError as exc:
        logger.error("matriz-client initialization failed: %s", exc)
        await _close_all(gateway, market_data)
        return 1
    logger.info("matriz-client initialized (base_url=%s)", settings.matriz_base_url)

    try:
        await asyncio.to_thread(market_data.connect)
    except MarketDataGatewayError as exc:
        logger.error("market-data-client initialization failed: %s", exc)
        await _close_all(gateway, market_data)
        return 1
    logger.info("market-data-client initialized (base_url=%s)", settings.market_data_base_url)

    while not stop.is_set():
        try:
            await asyncio.wait_for(stop.wait(), timeout=settings.worker_heartbeat_seconds)
        except TimeoutError:
            logger.info("worker heartbeat")

    await _close_all(gateway, market_data)
    logger.info("worker stopped")
    return 0


async def serve(
    gateway: MatrizGateway,
    market_data: MarketDataGateway,
    settings: WorkerSettings,
) -> int:
    """Corre `run` hasta recibir SIGINT o SIGTERM."""
    loop = asyncio.get_running_loop()
    stop = asyncio.Event()
    for sig in STOP_SIGNALS:
        loop.add_signal_handler(sig, stop.set)
    try:
        return await run(gateway, market_data, settings, stop)
    finally:
        for sig in STOP_SIGNALS:
            loop.remove_signal_handler(sig)
