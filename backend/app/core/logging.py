"""Logging estructurado con structlog: JSON en producción, consola legible en desarrollo.

Los logs de structlog y los de la stdlib (uvicorn, sqlalchemy, alembic) pasan por la misma
cadena de procesadores (`ProcessorFormatter`), así todos llevan `correlation_id` y redacción.
"""

import logging
import re
import sys
from collections.abc import Mapping
from typing import Final, Literal

import structlog
from asgi_correlation_id import correlation_id
from pydantic import SecretStr
from structlog.typing import EventDict, Processor, WrappedLogger

REDACTED: Final = "***"
SENSITIVE_KEY: Final = re.compile(r"password|token|secret|api_key", re.IGNORECASE)

# Loggers de terceros que traen handlers propios: se los vacía para que propaguen al root.
_PROPAGATED_LOGGERS: Final = ("uvicorn", "uvicorn.error", "uvicorn.access")


def _redact(value: object) -> object:
    if isinstance(value, SecretStr):
        return REDACTED
    if isinstance(value, Mapping):
        return {
            key: REDACTED if isinstance(key, str) and SENSITIVE_KEY.search(key) else _redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list | tuple):
        return type(value)(_redact(item) for item in value)
    return value


def redact_sensitive(_: WrappedLogger, __: str, event_dict: EventDict) -> EventDict:
    """Reemplaza por `"***"` los SecretStr y los valores de claves sensibles, también anidados."""
    for key, value in event_dict.items():
        if SENSITIVE_KEY.search(key):
            event_dict[key] = REDACTED
        else:
            event_dict[key] = _redact(value)
    return event_dict


def add_correlation_id(_: WrappedLogger, __: str, event_dict: EventDict) -> EventDict:
    """Agrega el `correlation_id` del request en curso (lo fija `CorrelationIdMiddleware`)."""
    request_id = correlation_id.get()
    if request_id is not None:
        event_dict.setdefault("correlation_id", request_id)
    return event_dict


def _shared_processors() -> list[Processor]:
    return [
        structlog.contextvars.merge_contextvars,
        add_correlation_id,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.ExtraAdder(),
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        redact_sensitive,
    ]


def _renderer_chain(app_env: Literal["development", "production"]) -> list[Processor]:
    if app_env == "production":
        return [structlog.processors.dict_tracebacks, structlog.processors.JSONRenderer()]
    return [structlog.dev.ConsoleRenderer()]


def configure_logging(app_env: Literal["development", "production"], log_level: str) -> None:
    """structlog + stdlib (uvicorn, sqlalchemy) vía ProcessorFormatter.

    JSONRenderer en `production`, ConsoleRenderer en otro caso.
    """
    shared = _shared_processors()
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            *shared,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=False,
    )
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            *_renderer_chain(app_env),
        ],
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(log_level.upper())
    for name in _PROPAGATED_LOGGERS:
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = True
