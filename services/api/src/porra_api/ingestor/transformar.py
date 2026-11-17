from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PartidoIngestado:
    football_data_id: int
    temporada: int
    fase: str
    jornada: int | None
    equipo_local: str | None
    equipo_visitante: str | None
    inicio: datetime
    estado: str
    goles_local: int | None
    goles_visitante: int | None


def _goles_a_los_90(score: dict) -> tuple[int | None, int | None]:
    """Goles al final del tiempo reglamentario (lo que cuenta en la porra)."""
    if score["duration"] == "REGULAR":
        resultado = score["fullTime"]
    else:
        resultado = score["regularTime"]
    return resultado["home"], resultado["away"]


def transformar_partido(dato: dict) -> PartidoIngestado:
    """Transforma un partido de la API de football-data.org en un PartidoIngestado."""
    goles_local, goles_visitante = _goles_a_los_90(dato["score"])
    return PartidoIngestado(
        football_data_id=dato["id"],
        temporada=int(dato["season"]["startDate"][:4]),
        fase=dato["stage"],
        jornada=dato["matchday"],
        equipo_local=dato["homeTeam"]["shortName"],
        equipo_visitante=dato["awayTeam"]["shortName"],
        inicio=datetime.fromisoformat(dato["utcDate"]),
        estado=dato["status"],
        goles_local=goles_local,
        goles_visitante=goles_visitante,
    )
