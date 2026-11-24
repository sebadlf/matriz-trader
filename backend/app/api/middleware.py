"""Middleware ASGI de log de acceso estructurado: un evento `request` por cada request HTTP."""

import time

import structlog
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = structlog.stdlib.get_logger("app.access")


class AccessLogMiddleware:
    """Loguea método, path, status y duración. Va dentro de `CorrelationIdMiddleware`."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = time.perf_counter()
        # Si la app lanza antes de responder, el 500 lo arma ServerErrorMiddleware (más afuera).
        status = 500

        async def send_with_status(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_with_status)
        finally:
            logger.info(
                "request",
                method=scope["method"],
                path=scope["path"],
                status=status,
                duration_ms=round((time.perf_counter() - start) * 1000, 2),
            )
