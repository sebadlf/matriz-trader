"""Probe de verify-guards: `datetime.now()` sin `tz` es una fecha naive (DTZ005)."""

from datetime import datetime


def ahora() -> datetime:
    return datetime.now()
