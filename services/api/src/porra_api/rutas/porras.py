from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from porra_api.clasificacion import FilaClasificacion, con_posiciones
from porra_api.dependencias import JugadorActual, SesionDep
from porra_api.models import Competicion, Jornada, Jugador, Miembro, Partido, Porra, Pronostico
from porra_api.puntuacion import PUNTOS_EXACTO
from porra_api.schemas import FilaClasificacionOut, PorraCrear, PorraOut, UnirsePorra, VincularChat
from porra_api.seguridad import generar_codigo_invitacion, normalizar_codigo

router = APIRouter(prefix="/porras", tags=["porras"])


def _salida(porra: Porra, codigo_competicion: str) -> PorraOut:
    return PorraOut(
        id=porra.id,
        nombre=porra.nombre,
        competicion=codigo_competicion,
        temporada=porra.temporada,
        codigo_invitacion=porra.codigo_invitacion,
    )


def _es_miembro(sesion: Session, porra_id: int, jugador_id: int) -> bool:
    return sesion.get(Miembro, (porra_id, jugador_id)) is not None


def _comprobar_que_puede_jugar(jugador: Jugador, competicion: Competicion) -> None:
    """Regla de negocio: La Máquina solo juega en ligas, donde su modelo tiene datos."""
    if jugador.es_maquina and competicion.tipo != "LEAGUE":
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "La Máquina solo puede jugar en competiciones de liga"
        )


@router.post("", response_model=PorraOut, status_code=status.HTTP_201_CREATED)
def crear_porra(datos: PorraCrear, jugador: JugadorActual, sesion: SesionDep):
    """Crea una porra; quien la crea es su primer miembro."""
    competicion = sesion.scalar(select(Competicion).where(Competicion.codigo == datos.competicion))
    if competicion is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "La competición no existe")
    _comprobar_que_puede_jugar(jugador, competicion)

    porra = Porra(
        nombre=datos.nombre,
        codigo_invitacion=generar_codigo_invitacion(),
        competicion_id=competicion.id,
        temporada=datos.temporada,
    )
    sesion.add(porra)
    sesion.flush()
    sesion.add(Miembro(porra_id=porra.id, jugador_id=jugador.id))
    sesion.commit()
    return _salida(porra, competicion.codigo)


@router.post("/unirse", response_model=PorraOut)
def unirse_a_porra(datos: UnirsePorra, jugador: JugadorActual, sesion: SesionDep):
    """Une al jugador a la porra del código. Unirse dos veces no hace nada (idempotente)."""
    fila = sesion.execute(
        select(Porra, Competicion)
        .join(Competicion)
        .where(Porra.codigo_invitacion == normalizar_codigo(datos.codigo))
    ).first()
    if fila is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No hay ninguna porra con ese código")
    porra, competicion = fila
    _comprobar_que_puede_jugar(jugador, competicion)

    sesion.execute(
        insert(Miembro).values(porra_id=porra.id, jugador_id=jugador.id).on_conflict_do_nothing()
    )
    sesion.commit()
    return _salida(porra, competicion.codigo)


@router.post("/chat", response_model=PorraOut)
def vincular_chat(datos: VincularChat, jugador: JugadorActual, sesion: SesionDep):
    """Asocia un chat de Telegram a una porra. Solo puede hacerlo uno de sus miembros."""
    fila = sesion.execute(
        select(Porra, Competicion)
        .join(Competicion)
        .where(Porra.codigo_invitacion == normalizar_codigo(datos.codigo))
    ).first()
    if fila is None or not _es_miembro(sesion, fila[0].id, jugador.id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No hay ninguna porra tuya con ese código")
    porra, competicion = fila

    porra.telegram_chat_id = datos.chat_id
    try:
        sesion.commit()
    except IntegrityError:
        sesion.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Este chat ya está vinculado a otra porra"
        ) from None
    return _salida(porra, competicion.codigo)


@router.get("/chat/{chat_id}", response_model=PorraOut)
def porra_del_chat(chat_id: int, jugador: JugadorActual, sesion: SesionDep):
    """La porra vinculada a un chat de Telegram, si el jugador es miembro."""
    fila = sesion.execute(
        select(Porra, Competicion.codigo).join(Competicion).where(Porra.telegram_chat_id == chat_id)
    ).first()
    if fila is None or not _es_miembro(sesion, fila[0].id, jugador.id):
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Este chat no está vinculado a ninguna porra tuya"
        )
    porra, codigo = fila
    return _salida(porra, codigo)


@router.get("", response_model=list[PorraOut])
def mis_porras(jugador: JugadorActual, sesion: SesionDep):
    """Las porras en las que participa el jugador."""
    filas = sesion.execute(
        select(Porra, Competicion.codigo)
        .join(Competicion)
        .join(Miembro, Miembro.porra_id == Porra.id)
        .where(Miembro.jugador_id == jugador.id)
        .order_by(Porra.id)
    ).all()
    return [_salida(porra, codigo) for porra, codigo in filas]


def _filas_clasificacion(sesion: Session, porra: Porra) -> list[FilaClasificacion]:
    """Puntos y exactos de cada miembro, contando solo la competición y temporada de la porra."""
    totales = (
        select(
            Pronostico.jugador_id,
            func.sum(Pronostico.puntos).label("puntos"),
            func.count().filter(Pronostico.puntos == PUNTOS_EXACTO).label("exactos"),
        )
        .join(Partido)
        .join(Jornada)
        .where(
            Jornada.competicion_id == porra.competicion_id,
            Jornada.temporada == porra.temporada,
        )
        .group_by(Pronostico.jugador_id)
        .subquery()
    )
    consulta = (
        select(
            Jugador.nombre,
            Jugador.es_maquina,
            func.coalesce(totales.c.puntos, 0),
            func.coalesce(totales.c.exactos, 0),
        )
        .join(Miembro, Miembro.jugador_id == Jugador.id)
        .outerjoin(totales, totales.c.jugador_id == Jugador.id)
        .where(Miembro.porra_id == porra.id)
    )
    return [
        FilaClasificacion(nombre=nombre, es_maquina=es_maquina, puntos=puntos, exactos=exactos)
        for nombre, es_maquina, puntos, exactos in sesion.execute(consulta)
    ]


@router.get("/{porra_id}/clasificacion", response_model=list[FilaClasificacionOut])
def clasificacion(porra_id: int, jugador: JugadorActual, sesion: SesionDep):
    """Clasificación de la porra. Solo la ven sus miembros; para los demás, no existe (404)."""
    porra = sesion.get(Porra, porra_id)
    if porra is None or not _es_miembro(sesion, porra_id, jugador.id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "La porra no existe")

    return [
        FilaClasificacionOut(
            posicion=posicion,
            nombre=fila.nombre,
            es_maquina=fila.es_maquina,
            puntos=fila.puntos,
            exactos=fila.exactos,
        )
        for posicion, fila in con_posiciones(_filas_clasificacion(sesion, porra))
    ]
