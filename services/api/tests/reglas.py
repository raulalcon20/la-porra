from datetime import UTC, datetime, timedelta

import pytest

from porra_api.reglas import Ventana, ventana_pronosticos

INICIO = datetime(2026, 12, 6, 20, 0, tzinfo=UTC)
UN_SEGUNDO = timedelta(seconds=1)
SIETE_DIAS = timedelta(days=7)


@pytest.mark.parametrize(
    ("ahora", "esperado"),
    [
        pytest.param(INICIO - timedelta(days=3), Ventana.ABIERTA, id="tres-dias-antes"),
        pytest.param(INICIO - UN_SEGUNDO, Ventana.ABIERTA, id="un-segundo-antes-del-inicio"),
        pytest.param(INICIO, Ventana.CERRADA, id="justo-al-empezar"),
        pytest.param(INICIO + timedelta(hours=1), Ventana.CERRADA, id="ya-empezado"),
        pytest.param(INICIO - SIETE_DIAS, Ventana.ABIERTA, id="justo-siete-dias-antes"),
        pytest.param(
            INICIO - SIETE_DIAS - UN_SEGUNDO, Ventana.NO_ABIERTA, id="un-segundo-antes-de-abrir"
        ),
        pytest.param(INICIO - timedelta(days=30), Ventana.NO_ABIERTA, id="un-mes-antes"),
    ],
)
def test_ventana_pronosticos(ahora, esperado):
    assert ventana_pronosticos(INICIO, ahora) == esperado
