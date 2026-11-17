import httpx
import pytest

from porra_api.ingestor.cliente import ClienteFootballData


def crear_cliente(manejador, esperas):
    """Cliente con la red y las esperas simuladas."""
    return ClienteFootballData(
        token="token-falso",
        base_url="https://api.test",
        transport=httpx.MockTransport(manejador),
        dormir=esperas.append,
    )


def test_envia_el_token_en_la_cabecera():
    recibidas = []

    def manejador(peticion):
        recibidas.append(peticion)
        return httpx.Response(200, json={"ok": True})

    cliente = crear_cliente(manejador, [])
    assert cliente.get("/competitions/PD") == {"ok": True}
    assert recibidas[0].headers["X-Auth-Token"] == "token-falso"


def test_tras_un_429_espera_lo_que_dice_el_servidor_y_reintenta():
    respuestas = iter(
        [
            httpx.Response(429, headers={"X-RequestCounter-Reset": "17"}),
            httpx.Response(200, json={"ok": True}),
        ]
    )
    esperas = []
    cliente = crear_cliente(lambda peticion: next(respuestas), esperas)
    assert cliente.get("/x") == {"ok": True}
    assert esperas == [17]


def test_se_frena_cuando_no_quedan_peticiones_en_el_minuto():
    esperas = []
    cabeceras = {"X-Requests-Available-Minute": "0", "X-RequestCounter-Reset": "30"}
    cliente = crear_cliente(
        lambda peticion: httpx.Response(200, json={}, headers=cabeceras), esperas
    )
    cliente.get("/x")
    assert esperas == [30]


def test_no_reintenta_los_errores_de_la_peticion():
    llamadas = []

    def manejador(peticion):
        llamadas.append(peticion)
        return httpx.Response(403)

    cliente = crear_cliente(manejador, [])
    with pytest.raises(httpx.HTTPStatusError):
        cliente.get("/x")
    assert len(llamadas) == 1
