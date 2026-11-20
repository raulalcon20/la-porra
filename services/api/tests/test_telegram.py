from datetime import UTC, datetime

from porra_api.config import get_settings

TELEGRAM_ANA = 1_234_567_890_123  # Más grande que un INTEGER de 32 bits
TELEGRAM_LUIS = 2_222_222_222
CHAT_DEL_GRUPO = -1_001_234_567_890  # Los grupos tienen ids negativos


def alta(cliente, como_bot, nombre="Ana", telegram_id=TELEGRAM_ANA):
    return cliente.post(
        "/jugadores/telegram",
        json={"nombre": nombre, "telegram_id": telegram_id},
        headers=como_bot(),
    )


def crear_porra_de(cliente, como_bot, telegram_id):
    respuesta = cliente.post(
        "/porras", json={"nombre": "El grupo", "temporada": 2026}, headers=como_bot(telegram_id)
    )
    return respuesta.json()["codigo_invitacion"]


def test_el_bot_da_de_alta_a_un_jugador(cliente, como_bot):
    respuesta = alta(cliente, como_bot)
    assert respuesta.status_code == 201
    assert respuesta.json()["nombre"] == "Ana"


def test_sin_el_secreto_del_bot_no_se_puede_dar_de_alta(cliente):
    datos = {"nombre": "Ana", "telegram_id": TELEGRAM_ANA}
    assert cliente.post("/jugadores/telegram", json=datos).status_code == 401
    respuesta = cliente.post("/jugadores/telegram", json=datos, headers={"X-Bot-Secreto": "falso"})
    assert respuesta.status_code == 401


def test_un_secreto_vacio_nunca_vale(cliente, monkeypatch):
    monkeypatch.setenv("PORRA_BOT_SECRETO", "")
    get_settings.cache_clear()
    datos = {"nombre": "Ana", "telegram_id": TELEGRAM_ANA}
    respuesta = cliente.post("/jugadores/telegram", json=datos, headers={"X-Bot-Secreto": ""})
    assert respuesta.status_code == 401


def test_el_bot_actua_en_nombre_del_usuario(cliente, como_bot):
    alta(cliente, como_bot)
    respuesta = cliente.get("/jugadores/yo", headers=como_bot(TELEGRAM_ANA))
    assert respuesta.status_code == 200
    assert respuesta.json()["nombre"] == "Ana"


def test_un_usuario_de_telegram_no_vinculado_da_401(cliente, como_bot):
    assert cliente.get("/jugadores/yo", headers=como_bot(999)).status_code == 401


def test_la_misma_cuenta_de_telegram_no_se_da_de_alta_dos_veces(cliente, como_bot):
    alta(cliente, como_bot)
    assert alta(cliente, como_bot, nombre="Otra").status_code == 409


def test_vincular_una_cuenta_que_ya_existe(cliente, como_bot):
    token = cliente.post("/jugadores", json={"nombre": "Luis"}).json()["token"]
    cabeceras = {
        **como_bot(),
        "Authorization": f"Bearer {token}",
        "X-Telegram-Usuario": str(TELEGRAM_LUIS),
    }

    assert cliente.post("/jugadores/yo/telegram", headers=cabeceras).status_code == 200
    respuesta = cliente.get("/jugadores/yo", headers=como_bot(TELEGRAM_LUIS))
    assert respuesta.json()["nombre"] == "Luis"


def test_sin_ser_el_bot_no_se_puede_vincular(cliente):
    token = cliente.post("/jugadores", json={"nombre": "Luis"}).json()["token"]
    cabeceras = {"Authorization": f"Bearer {token}", "X-Telegram-Usuario": str(TELEGRAM_LUIS)}
    assert cliente.post("/jugadores/yo/telegram", headers=cabeceras).status_code == 401


def test_vincular_el_chat_y_encontrar_su_porra(cliente, como_bot, crear_partido):
    crear_partido()  # Crea la competición PD
    alta(cliente, como_bot)
    codigo = crear_porra_de(cliente, como_bot, TELEGRAM_ANA)

    respuesta = cliente.post(
        "/porras/chat",
        json={"codigo": codigo, "chat_id": CHAT_DEL_GRUPO},
        headers=como_bot(TELEGRAM_ANA),
    )
    assert respuesta.status_code == 200

    respuesta = cliente.get(f"/porras/chat/{CHAT_DEL_GRUPO}", headers=como_bot(TELEGRAM_ANA))
    assert respuesta.status_code == 200
    assert respuesta.json()["nombre"] == "El grupo"


def test_quien_no_es_miembro_no_puede_vincular_el_chat(cliente, como_bot, crear_partido):
    crear_partido()
    alta(cliente, como_bot)
    alta(cliente, como_bot, nombre="Luis", telegram_id=TELEGRAM_LUIS)
    codigo = crear_porra_de(cliente, como_bot, TELEGRAM_ANA)

    respuesta = cliente.post(
        "/porras/chat",
        json={"codigo": codigo, "chat_id": CHAT_DEL_GRUPO},
        headers=como_bot(TELEGRAM_LUIS),
    )
    assert respuesta.status_code == 404


def test_proxima_jornada(cliente, crear_partido):
    crear_partido(jornada=1, estado="FINISHED")
    crear_partido(jornada=2, inicio=datetime(2026, 12, 13, 20, 0, tzinfo=UTC))
    crear_partido(jornada=3, inicio=datetime(2026, 12, 20, 20, 0, tzinfo=UTC))

    respuesta = cliente.get("/partidos/proxima-jornada")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"temporada": 2026, "jornada": 2}


def test_sin_partidos_pendientes_no_hay_proxima_jornada(cliente, crear_partido):
    crear_partido(estado="FINISHED")
    assert cliente.get("/partidos/proxima-jornada").status_code == 404
