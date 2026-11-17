from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from porra_api.ingestor.transformar import PartidoIngestado
from porra_api.models import Competicion, Jornada, Partido


def guardar_competicion(sesion: Session, codigo: str, nombre: str, tipo: str) -> int:
    """Upsert de la competición por su código. Devuelve su id."""
    sentencia = (
        insert(Competicion)
        .values(codigo=codigo, nombre=nombre, tipo=tipo)
        .on_conflict_do_update(index_elements=["codigo"], set_={"nombre": nombre, "tipo": tipo})
        .returning(Competicion.id)
    )
    return sesion.execute(sentencia).scalar_one()


def guardar_jornada(sesion: Session, competicion_id: int, partido: PartidoIngestado) -> int:
    """Upsert de la jornada (competición, temporada, fase, número). Devuelve su id."""
    sentencia = (
        insert(Jornada)
        .values(
            competicion_id=competicion_id,
            temporada=partido.temporada,
            fase=partido.fase,
            numero=partido.jornada,
        )
        .on_conflict_do_update(
            constraint="uq_jornadas_competicion_id_temporada_fase_numero",
            set_={"fase": partido.fase},
        )
        .returning(Jornada.id)
    )
    return sesion.execute(sentencia).scalar_one()


def guardar_partido(sesion: Session, jornada_id: int, partido: PartidoIngestado) -> None:
    """Upsert del partido por su football_data_id."""
    valores = {
        "football_data_id": partido.football_data_id,
        "jornada_id": jornada_id,
        "equipo_local": partido.equipo_local,
        "equipo_visitante": partido.equipo_visitante,
        "inicio": partido.inicio,
        "estado": partido.estado,
        "goles_local": partido.goles_local,
        "goles_visitante": partido.goles_visitante,
    }
    sentencia = insert(Partido).values(**valores)
    sentencia = sentencia.on_conflict_do_update(
        index_elements=["football_data_id"],
        set_={campo: sentencia.excluded[campo] for campo in valores if campo != "football_data_id"},
    )
    sesion.execute(sentencia)


def guardar_temporada(
    sesion: Session, competicion_id: int, partidos: list[PartidoIngestado]
) -> int:
    """Guarda todos los partidos (y sus jornadas). Devuelve cuántos ha guardado."""
    jornadas: dict[tuple, int] = {}
    for partido in partidos:
        clave = (partido.temporada, partido.fase, partido.jornada)
        if clave not in jornadas:
            jornadas[clave] = guardar_jornada(sesion, competicion_id, partido)
        guardar_partido(sesion, jornadas[clave], partido)
    return len(partidos)
