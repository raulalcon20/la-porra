from porra_api.models import Jugador, Pronostico
from porra_api.seguridad import hash_token
from porra_api.worker.puntuar import jornadas_por_puntuar, puntuar_jornada


def jugador(sesion, nombre):
    j = Jugador(nombre=nombre, token_hash=hash_token(nombre))
    sesion.add(j)
    sesion.flush()
    return j


def pronostico(sesion, jugador, partido, local, visitante):
    p = Pronostico(
        jugador_id=jugador.id, partido_id=partido.id, goles_local=local, goles_visitante=visitante
    )
    sesion.add(p)
    sesion.flush()
    return p


def terminar(sesion, partido, local, visitante):
    partido.estado = "FINISHED"
    partido.goles_local = local
    partido.goles_visitante = visitante
    sesion.flush()


def test_puntua_los_pronosticos_de_los_partidos_terminados(sesion, crear_partido):
    partido = crear_partido(jornada=1)
    exacto = pronostico(sesion, jugador(sesion, "Ana"), partido, 2, 1)
    signo = pronostico(sesion, jugador(sesion, "Luis"), partido, 1, 0)
    fallo = pronostico(sesion, jugador(sesion, "Marta"), partido, 0, 2)
    terminar(sesion, partido, 2, 1)

    assert puntuar_jornada(sesion, partido.jornada_id) == 3
    assert (exacto.puntos, signo.puntos, fallo.puntos) == (3, 1, 0)


def test_no_puntua_partidos_sin_terminar(sesion, crear_partido):
    partido = crear_partido(jornada=1, estado="TIMED")
    p = pronostico(sesion, jugador(sesion, "Ana"), partido, 2, 1)

    assert puntuar_jornada(sesion, partido.jornada_id) == 0
    assert p.puntos is None


def test_es_idempotente_y_corrige_si_cambia_el_resultado(sesion, crear_partido):
    partido = crear_partido(jornada=1)
    p = pronostico(sesion, jugador(sesion, "Ana"), partido, 2, 1)
    terminar(sesion, partido, 2, 1)

    puntuar_jornada(sesion, partido.jornada_id)
    puntuar_jornada(sesion, partido.jornada_id)
    assert p.puntos == 3

    terminar(sesion, partido, 2, 2)
    puntuar_jornada(sesion, partido.jornada_id)
    assert p.puntos == 0


def test_solo_puntua_su_jornada(sesion, crear_partido):
    de_la_1 = crear_partido(jornada=1)
    de_la_2 = crear_partido(jornada=2)
    ana = jugador(sesion, "Ana")
    p1 = pronostico(sesion, ana, de_la_1, 1, 0)
    p2 = pronostico(sesion, ana, de_la_2, 1, 0)
    terminar(sesion, de_la_1, 1, 0)
    terminar(sesion, de_la_2, 1, 0)

    puntuar_jornada(sesion, de_la_1.jornada_id)

    assert (p1.puntos, p2.puntos) == (3, None)


def test_jornadas_por_puntuar(sesion, crear_partido):
    terminado = crear_partido(jornada=1)
    sin_jugar = crear_partido(jornada=2, estado="TIMED")
    ana = jugador(sesion, "Ana")
    pronostico(sesion, ana, terminado, 1, 0)
    pronostico(sesion, ana, sin_jugar, 1, 0)
    terminar(sesion, terminado, 1, 0)

    assert jornadas_por_puntuar(sesion) == [terminado.jornada_id]

    puntuar_jornada(sesion, terminado.jornada_id)
    assert jornadas_por_puntuar(sesion) == []
