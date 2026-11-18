from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select

from porra_api.dependencias import get_ahora
from porra_api.main import app
from porra_api.models import Pronostico

INICIO = datetime(2026, 12, 6, 20, 0, tzinfo=UTC)
UN_DIA_ANTES = INICIO - timedelta(days=1)


def fijar_ahora(momento: datetime) -> None:
    """Hace que la API crea que la hora actual es `momento`."""
    app.dependency_overrides[get_ahora] = lambda: momento


def registrar(cliente, nombre: str) -> dict[str, str]:
    """Registra un jugador y devuelve sus cabeceras de autenticación."""
    token = cliente.post("/jugadores", json={"nombre": nombre}).json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def cabeceras(cliente):
    return registrar(cliente, "Ana")


def pronosticar(cliente, cabeceras, partido_id, local=2, visitante=1):
    return cliente.put(
        f"/pronosticos/{partido_id}",
        json={"goles_local": local, "goles_visitante": visitante},
        headers=cabeceras,
    )


def test_pronosticar_un_partido(cliente, cabeceras, crear_partido):
    partido = crear_partido(inicio=INICIO)
    fijar_ahora(UN_DIA_ANTES)

    respuesta = pronosticar(cliente, cabeceras, partido.id)

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "partido_id": partido.id,
        "goles_local": 2,
        "goles_visitante": 1,
        "puntos": None,
    }


def test_pronosticar_otra_vez_modifica_el_pronostico(cliente, cabeceras, crear_partido, sesion):
    partido = crear_partido(inicio=INICIO)
    fijar_ahora(UN_DIA_ANTES)

    pronosticar(cliente, cabeceras, partido.id, local=2, visitante=1)
    respuesta = pronosticar(cliente, cabeceras, partido.id, local=0, visitante=0)

    assert respuesta.json()["goles_local"] == 0
    assert sesion.scalar(select(func.count()).select_from(Pronostico)) == 1


def test_no_se_puede_pronosticar_un_partido_empezado(cliente, cabeceras, crear_partido):
    partido = crear_partido(inicio=INICIO)
    fijar_ahora(INICIO)
    assert pronosticar(cliente, cabeceras, partido.id).status_code == 409


def test_no_se_puede_pronosticar_antes_de_que_abra(cliente, cabeceras, crear_partido):
    partido = crear_partido(inicio=INICIO)
    fijar_ahora(INICIO - timedelta(days=8))
    assert pronosticar(cliente, cabeceras, partido.id).status_code == 409


def test_partido_sin_equipos_da_409(cliente, cabeceras, crear_partido):
    partido = crear_partido(inicio=INICIO, local=None, visitante=None)
    fijar_ahora(UN_DIA_ANTES)
    assert pronosticar(cliente, cabeceras, partido.id).status_code == 409


def test_partido_inexistente_da_404(cliente, cabeceras):
    fijar_ahora(UN_DIA_ANTES)
    assert pronosticar(cliente, cabeceras, 999_999).status_code == 404


def test_goles_negativos_da_422(cliente, cabeceras, crear_partido):
    partido = crear_partido(inicio=INICIO)
    fijar_ahora(UN_DIA_ANTES)
    assert pronosticar(cliente, cabeceras, partido.id, local=-1).status_code == 422


def test_sin_token_da_401(cliente, crear_partido):
    partido = crear_partido(inicio=INICIO)
    assert pronosticar(cliente, {}, partido.id).status_code == 401


def test_cada_jugador_solo_ve_sus_pronosticos(cliente, crear_partido):
    partido = crear_partido(inicio=INICIO)
    fijar_ahora(UN_DIA_ANTES)
    ana = registrar(cliente, "Ana")
    luis = registrar(cliente, "Luis")
    pronosticar(cliente, ana, partido.id, local=2, visitante=1)
    pronosticar(cliente, luis, partido.id, local=0, visitante=3)

    respuesta = cliente.get("/pronosticos", params={"temporada": 2026, "jornada": 1}, headers=ana)

    assert respuesta.status_code == 200
    assert [(p["goles_local"], p["goles_visitante"]) for p in respuesta.json()] == [(2, 1)]
