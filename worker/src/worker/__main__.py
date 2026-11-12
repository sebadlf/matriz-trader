"""Entrypoint `python -m worker` (AC-14, AC-15, AC-18)."""

import asyncio
import logging
import sys
from pathlib import Path

from pydantic import ValidationError

from model import missing_env_vars, root_env_file
from worker.market_data_gateway import MarketDataClientGateway
from worker.matriz_gateway import MatrizClientGateway
from worker.runner import serve
from worker.settings import WorkerSettings

logger = logging.getLogger("worker")

ENV_FILE = root_env_file()


def main(env_file: Path | None = ENV_FILE) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stdout,
    )
    try:
        settings = WorkerSettings(_env_file=env_file)  # pyright: ignore[reportCallIssue]
    except ValidationError as exc:
        missing = missing_env_vars(exc)
        if missing:
            logger.error("Missing required environment variables: %s", ", ".join(missing))
        else:
            logger.error("Invalid worker configuration: %s", exc)
        return 2
    logging.getLogger().setLevel(settings.log_level)
    return asyncio.run(
        serve(MatrizClientGateway(settings), MarketDataClientGateway(settings), settings)
    )


if __name__ == "__main__":
    sys.exit(main())
