from datetime import date

from porra_predictor.descarga import codigos_temporada


def test_en_noviembre_la_temporada_actual_es_la_que_empezo_ese_ano():
    assert codigos_temporada(date(2026, 11, 19), 3) == ["2425", "2526", "2627"]


def test_en_marzo_la_temporada_actual_es_la_que_empezo_el_ano_anterior():
    assert codigos_temporada(date(2027, 3, 1), 2) == ["2526", "2627"]


def test_el_cambio_de_siglo():
    assert codigos_temporada(date(2099, 9, 1), 1) == ["9900"]
