"""Entrypoint: `python -m app [--reload]`. Valida la configuración antes de levantar uvicorn."""

import argparse
from collections.abc import Sequence

import uvicorn

from app.core.config import load_settings
from app.core.logging import configure_logging


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m app", description="Backend de matriz-trader")
    parser.add_argument("--reload", action="store_true", help="recarga ante cambios en app/")
    args = parser.parse_args(argv)

    settings = load_settings()
    configure_logging(settings.app_env, settings.log_level)
    # Sin `log_config=None`, uvicorn reaplica su dictConfig y pisa la configuración de structlog.
    uvicorn.run(
        "app.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=args.reload,
        reload_dirs=["app"],
        log_level=settings.log_level,
        log_config=None,
        access_log=False,
    )


if __name__ == "__main__":
    main()
