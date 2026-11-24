"""Probe de verify-guards: `time.sleep` dentro de `async def` bloquea el event loop (ASYNC251)."""

import time


async def esperar() -> None:
    time.sleep(1)
