from datetime import UTC, datetime


def test_lista_los_partidos_de_la_jornada_ordenados_por_hora(cliente, crear_partido):
    crear_partido(jornada=1, inicio=datetime(2026, 12, 6, 21, 0, tzinfo=UTC), local="Madrid")
    crear_partido(jornada=1, inicio=datetime(2026, 12, 6, 16, 0, tzinfo=UTC), local="Betis")
    crear_partido(jornada=2, local="Girona")

    respuesta = cliente.get("/partidos", params={"temporada": 2026, "jornada": 1})

    assert respuesta.status_code == 200
    locales = [partido["equipo_local"] for partido in respuesta.json()]
    assert locales == ["Betis", "Madrid"]


def test_jornada_no_numerica_da_422(cliente):
    respuesta = cliente.get("/partidos", params={"temporada": 2026, "jornada": "trece"})
    assert respuesta.status_code == 422
