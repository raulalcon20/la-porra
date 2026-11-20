import secrets
from collections.abc import Iterator
from datetime import UTC, datetime
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
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
CredencialesDep = Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]


def _no_autenticado(mensaje: str) -> HTTPException:
    return HTTPException(
        status.HTTP_401_UNAUTHORIZED, mensaje, headers={"WWW-Authenticate": "Bearer"}
    )


def verificar_bot(x_bot_secreto: Annotated[str | None, Header()] = None) -> None:
    """La petición viene del bot. Si el bot no está configurado, nadie puede serlo."""
    esperado = get_settings().bot_secreto
    if (
        x_bot_secreto is None
        or esperado is None
        or not esperado.get_secret_value()
        or not secrets.compare_digest(x_bot_secreto.encode(), esperado.get_secret_value().encode())
    ):
        raise _no_autenticado("Credenciales del bot no válidas")


def get_jugador_por_token(sesion: SesionDep, credenciales: CredencialesDep) -> Jugador:
    """El jugador al que pertenece el token de la cabecera Authorization."""
    if credenciales is None:
        raise _no_autenticado("Falta el token")
    jugador = sesion.scalar(
        select(Jugador).where(Jugador.token_hash == hash_token(credenciales.credentials))
    )
    if jugador is None:
        raise _no_autenticado("Token no válido")
    return jugador


def get_jugador_actual(
    sesion: SesionDep,
    credenciales: CredencialesDep,
    x_bot_secreto: Annotated[str | None, Header()] = None,
    x_telegram_usuario: Annotated[int | None, Header()] = None,
) -> Jugador:
    """El jugador de la petición: por su token o, si llama el bot, por su usuario de Telegram."""
    if x_bot_secreto is None:
        return get_jugador_por_token(sesion, credenciales)

    verificar_bot(x_bot_secreto)
    if x_telegram_usuario is None:
        raise _no_autenticado("Falta el usuario de Telegram")
    jugador = sesion.scalar(select(Jugador).where(Jugador.telegram_id == x_telegram_usuario))
    if jugador is None:
        raise _no_autenticado("Este usuario de Telegram no está vinculado a ningún jugador")
    return jugador


JugadorPorToken = Annotated[Jugador, Depends(get_jugador_por_token)]
JugadorActual = Annotated[Jugador, Depends(get_jugador_actual)]
