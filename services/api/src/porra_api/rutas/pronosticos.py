from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from porra_api.dependencias import AhoraDep, JugadorActual, SesionDep
from porra_api.models import Competicion, Jornada, Partido, Pronostico
from porra_api.reglas import Ventana, ventana_pronosticos
from porra_api.schemas import PronosticoIn, PronosticoOut

router = APIRouter(prefix="/pronosticos", tags=["pronosticos"])

MENSAJES_VENTANA = {
    Ventana.CERRADA: "El partido ya ha empezado: no se admiten pronósticos",
    Ventana.NO_ABIERTA: "Todavía no se puede pronosticar: se abre 7 días antes del partido",
}


@router.put("/{partido_id}", response_model=PronosticoOut)
def pronosticar(
    partido_id: int,
    datos: PronosticoIn,
    jugador: JugadorActual,
    sesion: SesionDep,
    ahora: AhoraDep,
):
    """Crea o modifica el pronóstico del jugador para un partido."""
    partido = sesion.get(Partido, partido_id)
    if partido is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El partido no existe")
    if partido.equipo_local is None or partido.equipo_visitante is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "El partido todavía no tiene equipos")

    ventana = ventana_pronosticos(partido.inicio, ahora)
    if ventana is not Ventana.ABIERTA:
        raise HTTPException(status.HTTP_409_CONFLICT, MENSAJES_VENTANA[ventana])

    sentencia = (
        insert(Pronostico)
        .values(
            jugador_id=jugador.id,
            partido_id=partido.id,
            goles_local=datos.goles_local,
            goles_visitante=datos.goles_visitante,
        )
        .on_conflict_do_update(
            index_elements=["jugador_id", "partido_id"],
            set_={"goles_local": datos.goles_local, "goles_visitante": datos.goles_visitante},
        )
        .returning(Pronostico)
    )
    pronostico = sesion.scalars(sentencia).one()
    sesion.commit()
    return pronostico


@router.get("", response_model=list[PronosticoOut])
def mis_pronosticos(
    jugador: JugadorActual,
    sesion: SesionDep,
    temporada: int,
    jornada: int,
    competicion: str = "PD",
):
    """Los pronósticos del jugador para una jornada."""
    consulta = (
        select(Pronostico)
        .join(Partido)
        .join(Jornada)
        .join(Competicion)
        .where(
            Pronostico.jugador_id == jugador.id,
            Competicion.codigo == competicion,
            Jornada.temporada == temporada,
            Jornada.numero == jornada,
        )
        .order_by(Partido.inicio)
    )
    return sesion.scalars(consulta).all()
