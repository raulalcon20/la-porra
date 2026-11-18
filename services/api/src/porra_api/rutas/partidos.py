from fastapi import APIRouter
from sqlalchemy import select

from porra_api.dependencias import SesionDep
from porra_api.models import Competicion, Jornada, Partido
from porra_api.schemas import PartidoOut

router = APIRouter(prefix="/partidos", tags=["partidos"])


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
