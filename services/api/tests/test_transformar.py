import copy
from datetime import UTC, datetime

from porra_api.ingestor.transformar import transformar_partido

PARTIDO_TERMINADO = {
    "id": 564634,
    "utcDate": "2026-08-15T17:30:00Z",
    "status": "FINISHED",
    "matchday": 1,
    "stage": "REGULAR_SEASON",
    "season": {"startDate": "2026-08-16"},
    "homeTeam": {"shortName": "Alavés"},
    "awayTeam": {"shortName": "Getafe"},
    "score": {"duration": "REGULAR", "fullTime": {"home": 3, "away": 0}},
}


def con_cambios(**cambios):
    """Copia del partido terminado con algunos campos cambiados."""
    dato = copy.deepcopy(PARTIDO_TERMINADO)
    dato.update(cambios)
    return dato


def test_partido_terminado():
    p = transformar_partido(PARTIDO_TERMINADO)
    assert p.football_data_id == 564634
    assert p.temporada == 2026
    assert p.fase == "REGULAR_SEASON"
    assert p.jornada == 1
    assert p.equipo_local == "Alavés"
    assert p.equipo_visitante == "Getafe"
    assert p.inicio == datetime(2026, 8, 15, 17, 30, tzinfo=UTC)
    assert p.estado == "FINISHED"
    assert (p.goles_local, p.goles_visitante) == (3, 0)


def test_partido_sin_jugar_no_tiene_goles():
    dato = con_cambios(
        status="TIMED",
        score={"duration": "REGULAR", "fullTime": {"home": None, "away": None}},
    )
    p = transformar_partido(dato)
    assert (p.goles_local, p.goles_visitante) == (None, None)


def test_eliminatoria_sin_sorteo_no_tiene_equipos_ni_jornada():
    dato = con_cambios(
        stage="LAST_16",
        matchday=None,
        homeTeam={"shortName": None},
        awayTeam={"shortName": None},
    )
    p = transformar_partido(dato)
    assert p.jornada is None
    assert p.equipo_local is None
    assert p.equipo_visitante is None


def test_con_prorroga_cuenta_el_resultado_de_los_90_minutos():
    dato = con_cambios(
        score={
            "duration": "EXTRA_TIME",
            "fullTime": {"home": 2, "away": 1},
            "regularTime": {"home": 1, "away": 1},
        },
    )
    p = transformar_partido(dato)
    assert (p.goles_local, p.goles_visitante) == (1, 1)
