from fastapi import APIRouter
from sqlalchemy import select

from porra_api.dependencias import SesionDep
from porra_api.models import Competicion
from porra_api.schemas import CompeticionOut

router = APIRouter(prefix="/competiciones", tags=["competiciones"])


@router.get("", response_model=list[CompeticionOut])
def listar_competiciones(sesion: SesionDep):
    return sesion.scalars(select(Competicion).order_by(Competicion.codigo)).all()
