"""Dependencias de FastAPI compartidas por las rutas.

Es la única puerta de `app.api` hacia la base de datos (contrato de import-linter
«API sin acceso directo a la DB»).
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock, get_clock
from app.db.session import get_session

SessionDep = Annotated[AsyncSession, Depends(get_session)]
ClockDep = Annotated[Clock, Depends(get_clock)]
