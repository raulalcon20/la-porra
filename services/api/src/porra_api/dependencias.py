from collections.abc import Iterator
from datetime import UTC, datetime
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from porra_api.config import get_settings
from porra_api.db import crear_sesiones
from porra_api.models import Jugador
from porra_api.seguridad import hash_token


@lru_cache
def _fabrica_sesiones() -> sessionmaker[Session]:
    return crear_sesiones(get_settings().database_url)


def get_sesion() -> Iterator[Session]:
    """Una sesión por petición, que se cierra siempre al terminar."""
    with _fabrica_sesiones()() as sesion:
        yield sesion


SesionDep = Annotated[Session, Depends(get_sesion)]


def get_ahora() -> datetime:
    """La hora actual en UTC. Es una dependencia para que los tests puedan fijarla."""
    return datetime.now(UTC)


AhoraDep = Annotated[datetime, Depends(get_ahora)]

_bearer = HTTPBearer(auto_error=False)


def get_jugador_actual(
    sesion: SesionDep,
    credenciales: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Jugador:
    """El jugador al que pertenece el token de la cabecera Authorization."""
    if credenciales is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Falta el token", headers={"WWW-Authenticate": "Bearer"}
        )
    jugador = sesion.scalar(
        select(Jugador).where(Jugador.token_hash == hash_token(credenciales.credentials))
    )
    if jugador is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Token no válido", headers={"WWW-Authenticate": "Bearer"}
        )
    return jugador


JugadorActual = Annotated[Jugador, Depends(get_jugador_actual)]
