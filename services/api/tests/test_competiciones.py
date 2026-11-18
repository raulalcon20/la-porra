from porra_api.models import Competicion


def test_listar_competiciones(cliente, sesion):
    sesion.add(Competicion(codigo="PD", nombre="LaLiga", tipo="LEAGUE"))
    sesion.flush()

    respuesta = cliente.get("/competiciones")

    assert respuesta.status_code == 200
    assert respuesta.json() == [{"codigo": "PD", "nombre": "LaLiga", "tipo": "LEAGUE"}]
