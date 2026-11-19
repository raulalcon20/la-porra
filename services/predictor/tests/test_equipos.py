import pytest

from porra_predictor.equipos import EQUIVALENCIAS, EquipoDesconocido, nombre_en_modelo


def test_traduce_el_nombre_de_la_api():
    assert nombre_en_modelo("Atleti") == "Ath Madrid"


def test_un_equipo_que_no_esta_en_la_tabla_falla():
    with pytest.raises(EquipoDesconocido):
        nombre_en_modelo("Inventado CF")


def test_no_hay_dos_equipos_con_el_mismo_nombre_en_el_modelo():
    assert len(set(EQUIVALENCIAS.values())) == len(EQUIVALENCIAS)
