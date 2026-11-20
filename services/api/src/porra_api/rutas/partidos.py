from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from porra_api.dependencias import SesionDep
from porra_api.models import Competicion, Jornada, Partido
from porra_api.schemas import PartidoOut, ProximaJornadaOut

router = APIRouter(prefix="/partidos", tags=["partidos"])

ESTADOS_PENDIENTES = ("SCHEDULED", "TIMED")


@router.get("", response_model=list[PartidoOut])
def listar_partidos(sesion: SesionDep, temporada: int, jornada: int, competicion: str = "PD"):
    """Partidos de una jornada, ordenados por hora de inicio."""
    consulta = (
        select(Partido)
        .join(Jornada)
        .join(Competicion)
        .where(
            Competicion.codigo == competicion,
            Jornada.temporada == temporada,
            Jornada.numero == jornada,
        )
        .order_by(Partido.inicio)
    )
    return sesion.scalars(consulta).all()


@router.get("/proxima-jornada", response_model=ProximaJornadaOut)
def proxima_jornada(sesion: SesionDep, competicion: str = "PD"):
    """La jornada del próximo partido pendiente de jugarse."""
    fila = sesion.execute(
        select(Jornada.temporada, Jornada.numero)
        .select_from(Partido)
        .join(Jornada)
        .join(Competicion)
        .where(
            Competicion.codigo == competicion,
            Partido.estado.in_(ESTADOS_PENDIENTES),
            Jornada.numero.is_not(None),
        )
        .order_by(Partido.inicio)
        .limit(1)
    ).first()
    if fila is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No quedan partidos pendientes")
    return ProximaJornadaOut(temporada=fila.temporada, jornada=fila.numero)
