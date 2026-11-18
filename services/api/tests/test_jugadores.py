from sqlalchemy import select

from porra_api.models import Jugador
from porra_api.seguridad import hash_token


def crear(cliente, nombre="Ana"):
    return cliente.post("/jugadores", json={"nombre": nombre})


def test_crear_jugador_devuelve_su_token(cliente):
    respuesta = crear(cliente)
    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert datos["nombre"] == "Ana"
    assert datos["es_maquina"] is False
    assert len(datos["token"]) > 30


def test_nombre_repetido_da_409(cliente):
    crear(cliente)
    assert crear(cliente).status_code == 409


def test_nombre_vacio_da_422(cliente):
    assert crear(cliente, nombre="   ").status_code == 422


def test_nadie_puede_registrarse_como_maquina(cliente):
    respuesta = cliente.post("/jugadores", json={"nombre": "Tramposo", "es_maquina": True})
    assert respuesta.status_code == 201
    assert respuesta.json()["es_maquina"] is False


def test_la_base_de_datos_guarda_el_hash_y_no_el_token(cliente, sesion):
    token = crear(cliente).json()["token"]
    jugador = sesion.scalar(select(Jugador).where(Jugador.nombre == "Ana"))
    assert jugador.token_hash != token
    assert jugador.token_hash == hash_token(token)


def test_quien_soy_con_token_valido(cliente):
    token = crear(cliente).json()["token"]
    respuesta = cliente.get("/jugadores/yo", headers={"Authorization": f"Bearer {token}"})
    assert respuesta.status_code == 200
    assert respuesta.json()["nombre"] == "Ana"


def test_quien_soy_sin_token_da_401(cliente):
    assert cliente.get("/jugadores/yo").status_code == 401


def test_quien_soy_con_token_falso_da_401(cliente):
    respuesta = cliente.get("/jugadores/yo", headers={"Authorization": "Bearer token-falso"})
    assert respuesta.status_code == 401
