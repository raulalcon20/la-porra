from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.exc import IntegrityError

from porra_api.dependencias import JugadorActual, JugadorPorToken, SesionDep, verificar_bot
from porra_api.models import Jugador
from porra_api.schemas import JugadorCreado, JugadorCrear, JugadorOut, JugadorTelegramCrear
from porra_api.seguridad import generar_token, hash_token

router = APIRouter(prefix="/jugadores", tags=["jugadores"])


@router.post("", response_model=JugadorCreado, status_code=status.HTTP_201_CREATED)
def crear_jugador(datos: JugadorCrear, sesion: SesionDep):
    token = generar_token()
    jugador = Jugador(nombre=datos.nombre, token_hash=hash_token(token))
    sesion.add(jugador)
    try:
        sesion.commit()
    except IntegrityError:
        sesion.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"Ya existe un jugador llamado {datos.nombre!r}"
        ) from None
    sesion.refresh(jugador)
    return JugadorCreado(
        id=jugador.id, nombre=jugador.nombre, es_maquina=jugador.es_maquina, token=token
    )


@router.post(
    "/telegram",
    response_model=JugadorOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verificar_bot)],
)
def crear_jugador_telegram(datos: JugadorTelegramCrear, sesion: SesionDep):
    """Solo el bot: da de alta a un jugador ya vinculado a su cuenta de Telegram."""
    # El jugador tiene un token que nadie conoce; si algún día lo necesita, se le genera uno nuevo.
    jugador = Jugador(
        nombre=datos.nombre, telegram_id=datos.telegram_id, token_hash=hash_token(generar_token())
    )
    sesion.add(jugador)
    try:
        sesion.commit()
    except IntegrityError:
        sesion.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Ya existe un jugador con ese nombre o con esa cuenta de Telegram",
        ) from None
    sesion.refresh(jugador)
    return jugador


@router.post("/yo/telegram", response_model=JugadorOut, dependencies=[Depends(verificar_bot)])
def vincular_telegram(
    jugador: JugadorPorToken,
    sesion: SesionDep,
    x_telegram_usuario: Annotated[int, Header()],
):
    """Solo el bot: vincula la cuenta de Telegram al jugador dueño del token."""
    jugador.telegram_id = x_telegram_usuario
    try:
        sesion.commit()
    except IntegrityError:
        sesion.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Esa cuenta de Telegram ya está vinculada a otro jugador"
        ) from None
    return jugador


@router.get("/yo", response_model=JugadorOut)
def quien_soy(jugador: JugadorActual):
    return jugador
