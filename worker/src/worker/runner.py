"""Loop long-running del worker con apagado ordenado por señales (AC-14, AC-15, AC-17)."""

import asyncio
import logging
import signal

from worker.matriz_gateway import GatewayError, MatrizGateway
from worker.settings import WorkerSettings

logger = logging.getLogger(__name__)

CLOSE_TIMEOUT_SECONDS = 5.0
STOP_SIGNALS = (signal.SIGINT, signal.SIGTERM)


async def _close(gateway: MatrizGateway) -> None:
    try:
        await asyncio.wait_for(asyncio.to_thread(gateway.close), CLOSE_TIMEOUT_SECONDS)
    except Exception:
        logger.exception("matriz-client close failed")


async def run(gateway: MatrizGateway, settings: WorkerSettings, stop: asyncio.Event) -> int:
    try:
        await asyncio.to_thread(gateway.connect)
    except GatewayError as exc:
        logger.error("matriz-client initialization failed: %s", exc)
        await _close(gateway)
        return 1
    logger.info("matriz-client initialized (base_url=%s)", settings.matriz_base_url)

    while not stop.is_set():
        try:
            await asyncio.wait_for(stop.wait(), timeout=settings.worker_heartbeat_seconds)
        except TimeoutError:
            logger.info("worker heartbeat")

    await _close(gateway)
    logger.info("worker stopped")
    return 0


async def serve(gateway: MatrizGateway, settings: WorkerSettings) -> int:
    """Corre `run` hasta recibir SIGINT o SIGTERM."""
    loop = asyncio.get_running_loop()
    stop = asyncio.Event()
    for sig in STOP_SIGNALS:
        loop.add_signal_handler(sig, stop.set)
    try:
        return await run(gateway, settings, stop)
    finally:
        for sig in STOP_SIGNALS:
            loop.remove_signal_handler(sig)
