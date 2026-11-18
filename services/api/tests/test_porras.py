from datetime import UTC, datetime

import pytest
from sqlalchemy import func, select

from porra_api.models import Competicion, Jornada, Jugador, Miembro, Partido, Pronostico
from porra_api.seguridad import ALFABETO_INVITACION, generar_token, hash_token


def registrar(cliente, nombre):
    """Registra un jugador y devuelve su id y sus cabeceras de autenticación."""
    datos = cliente.post("/jugadores", json={"nombre": nombre}).json()
    return datos["id"], {"Authorization": f"Bearer {datos['token']}"}


def crear_porra(cliente, cabeceras, competicion="PD"):
    return cliente.post(
        "/porras",
        json={"nombre": "Los del pueblo", "temporada": 2026, "competicion": competicion},
        headers=cabeceras,
    )


@pytest.fixture
def ana(cliente, crear_partido):
    """Ana, ya registrada. Pedir `crear_partido` asegura que existe la competición PD."""
    return registrar(cliente, "Ana")


@pytest.fixture
def maquina(sesion):
    """La Máquina se crea directamente en la base de datos: por la API es imposible."""
    token = generar_token()
    sesion.add(Jugador(nombre="La Máquina", es_maquina=True, token_hash=hash_token(token)))
    sesion.flush()
    return {"Authorization": f"Bearer {token}"}


def test_crear_porra(cliente, ana):
    _, cabeceras = ana
    respuesta = crear_porra(cliente, cabeceras)

    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert datos["competicion"] == "PD"
    assert len(datos["codigo_invitacion"]) == 8
    assert set(datos["codigo_invitacion"]) <= set(ALFABETO_INVITACION)


def test_quien_crea_la_porra_es_miembro(cliente, ana):
    _, cabeceras = ana
    crear_porra(cliente, cabeceras)
    respuesta = cliente.get("/porras", headers=cabeceras)
    assert [p["nombre"] for p in respuesta.json()] == ["Los del pueblo"]


def test_competicion_inexistente_da_404(cliente, ana):
    _, cabeceras = ana
    assert crear_porra(cliente, cabeceras, competicion="XYZ").status_code == 404


def test_unirse_con_el_codigo_aunque_se_escriba_en_minusculas(cliente, ana):
    _, cabeceras_ana = ana
    codigo = crear_porra(cliente, cabeceras_ana).json()["codigo_invitacion"]
    _, cabeceras_luis = registrar(cliente, "Luis")

    respuesta = cliente.post(
        "/porras/unirse", json={"codigo": f"  {codigo.lower()} "}, headers=cabeceras_luis
    )

    assert respuesta.status_code == 200
    assert len(cliente.get("/porras", headers=cabeceras_luis).json()) == 1


def test_unirse_dos_veces_no_duplica(cliente, ana, sesion):
    _, cabeceras_ana = ana
    codigo = crear_porra(cliente, cabeceras_ana).json()["codigo_invitacion"]
    _, cabeceras_luis = registrar(cliente, "Luis")

    cliente.post("/porras/unirse", json={"codigo": codigo}, headers=cabeceras_luis)
    respuesta = cliente.post("/porras/unirse", json={"codigo": codigo}, headers=cabeceras_luis)

    assert respuesta.status_code == 200
    assert sesion.scalar(select(func.count()).select_from(Miembro)) == 2


def test_codigo_inexistente_da_404(cliente, ana):
    _, cabeceras = ana
    respuesta = cliente.post("/porras/unirse", json={"codigo": "NOEXISTE"}, headers=cabeceras)
    assert respuesta.status_code == 404


def test_la_maquina_puede_unirse_a_una_liga(cliente, ana, maquina):
    _, cabeceras_ana = ana
    codigo = crear_porra(cliente, cabeceras_ana).json()["codigo_invitacion"]
    respuesta = cliente.post("/porras/unirse", json={"codigo": codigo}, headers=maquina)
    assert respuesta.status_code == 200


def test_la_maquina_no_puede_unirse_a_una_copa(cliente, ana, maquina, sesion):
    sesion.add(Competicion(codigo="CL", nombre="Champions League", tipo="CUP"))
    sesion.flush()
    _, cabeceras_ana = ana
    codigo = crear_porra(cliente, cabeceras_ana, competicion="CL").json()["codigo_invitacion"]

    respuesta = cliente.post("/porras/unirse", json={"codigo": codigo}, headers=maquina)

    assert respuesta.status_code == 403


def test_clasificacion(cliente, ana, sesion, crear_partido):
    id_ana, cabeceras_ana = ana
    porra = crear_porra(cliente, cabeceras_ana).json()
    id_luis, cabeceras_luis = registrar(cliente, "Luis")
    _, cabeceras_marta = registrar(cliente, "Marta")
    for cabeceras in (cabeceras_luis, cabeceras_marta):
        cliente.post(
            "/porras/unirse", json={"codigo": porra["codigo_invitacion"]}, headers=cabeceras
        )

    # Dos partidos de LaLiga 2026, ya puntuados (el worker aún no existe: puntos a mano)
    p1 = crear_partido(jornada=1)
    p2 = crear_partido(jornada=2)
    sesion.add_all(
        [
            Pronostico(
                jugador_id=id_ana, partido_id=p1.id, goles_local=2, goles_visitante=1, puntos=3
            ),
            Pronostico(
                jugador_id=id_ana, partido_id=p2.id, goles_local=1, goles_visitante=0, puntos=1
            ),
            Pronostico(
                jugador_id=id_luis, partido_id=p1.id, goles_local=2, goles_visitante=1, puntos=3
            ),
            Pronostico(
                jugador_id=id_luis, partido_id=p2.id, goles_local=0, goles_visitante=0, puntos=None
            ),
        ]
    )
    # Un partido de otra competición: no debe contar en esta porra
    otra = Competicion(codigo="CL", nombre="Champions League", tipo="CUP")
    sesion.add(otra)
    sesion.flush()
    jornada_cl = Jornada(competicion_id=otra.id, temporada=2026, fase="LEAGUE_STAGE", numero=1)
    sesion.add(jornada_cl)
    sesion.flush()
    partido_cl = Partido(
        football_data_id=999,
        jornada_id=jornada_cl.id,
        equipo_local="Madrid",
        equipo_visitante="City",
        inicio=datetime(2026, 12, 9, 20, 0, tzinfo=UTC),
        estado="FINISHED",
    )
    sesion.add(partido_cl)
    sesion.flush()
    sesion.add(
        Pronostico(
            jugador_id=id_luis, partido_id=partido_cl.id, goles_local=1, goles_visitante=1, puntos=3
        )
    )
    sesion.flush()

    respuesta = cliente.get(f"/porras/{porra['id']}/clasificacion", headers=cabeceras_ana)

    assert respuesta.status_code == 200
    filas = [(f["posicion"], f["nombre"], f["puntos"], f["exactos"]) for f in respuesta.json()]
    assert filas == [(1, "Ana", 4, 1), (2, "Luis", 3, 1), (3, "Marta", 0, 0)]


def test_quien_no_es_miembro_no_ve_la_clasificacion(cliente, ana):
    _, cabeceras_ana = ana
    porra = crear_porra(cliente, cabeceras_ana).json()
    _, cabeceras_intruso = registrar(cliente, "Intruso")

    respuesta = cliente.get(f"/porras/{porra['id']}/clasificacion", headers=cabeceras_intruso)

    assert respuesta.status_code == 404
