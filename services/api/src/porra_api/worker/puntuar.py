from sqlalchemy import select
from sqlalchemy.orm import Session

from porra_api.models import Partido, Pronostico
from porra_api.puntuacion import puntuar

ESTADO_TERMINADO = "FINISHED"


def _partido_con_resultado():
    """Condición de un partido que ya se puede puntuar."""
    return (
        Partido.estado == ESTADO_TERMINADO,
        Partido.goles_local.is_not(None),
        Partido.goles_visitante.is_not(None),
    )


def puntuar_jornada(sesion: Session, jornada_id: int) -> int:
    """Recalcula los puntos de los pronósticos de los partidos terminados de una jornada.

    Es idempotente: recalcula siempre a partir del resultado, así que ejecutarla dos
    veces da lo mismo que una, y si se corrige un resultado, corrige los puntos.
    Devuelve cuántos pronósticos ha puntuado.
    """
    filas = sesion.execute(
        select(Pronostico, Partido)
        .join(Partido)
        .where(Partido.jornada_id == jornada_id, *_partido_con_resultado())
    ).all()
    for pronostico, partido in filas:
        pronostico.puntos = puntuar(
            (pronostico.goles_local, pronostico.goles_visitante),
            (partido.goles_local, partido.goles_visitante),
        )
    return len(filas)


def jornadas_por_puntuar(sesion: Session) -> list[int]:
    """Jornadas con algún partido terminado que tiene pronósticos aún sin puntuar."""
    consulta = (
        select(Partido.jornada_id)
        .join(Pronostico)
        .where(Pronostico.puntos.is_(None), *_partido_con_resultado())
        .distinct()
        .order_by(Partido.jornada_id)
    )
    return list(sesion.scalars(consulta))
