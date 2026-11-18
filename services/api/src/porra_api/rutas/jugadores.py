from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError

from porra_api.dependencias import JugadorActual, SesionDep
from porra_api.models import Jugador
from porra_api.schemas import JugadorCreado, JugadorCrear, JugadorOut
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


@router.get("/yo", response_model=JugadorOut)
def quien_soy(jugador: JugadorActual):
    return jugador
