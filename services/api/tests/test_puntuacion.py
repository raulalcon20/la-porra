import pytest

from porra_api.puntuacion import PUNTOS_EXACTO, PUNTOS_SIGNO, puntuar


@pytest.mark.parametrize(
    ("pronostico", "resultado", "esperado"),
    [
        # Resultado exacto
        pytest.param((2, 1), (2, 1), PUNTOS_EXACTO, id="exacto-gana-local"),
        pytest.param((1, 1), (1, 1), PUNTOS_EXACTO, id="exacto-empate"),
        pytest.param((0, 2), (0, 2), PUNTOS_EXACTO, id="exacto-gana-visitante"),
        pytest.param((0, 0), (0, 0), PUNTOS_EXACTO, id="exacto-0-0"),
        # Signo acertado sin resultado exacto
        pytest.param((1, 0), (3, 1), PUNTOS_SIGNO, id="signo-1"),
        pytest.param((0, 0), (2, 2), PUNTOS_SIGNO, id="signo-X"),
        pytest.param((1, 2), (0, 4), PUNTOS_SIGNO, id="signo-2"),
        pytest.param((2, 1), (3, 2), PUNTOS_SIGNO, id="misma-diferencia-no-es-exacto"),
        # Fallos
        pytest.param((2, 0), (0, 1), 0, id="pronostica-1-gana-visitante"),
        pytest.param((1, 1), (2, 0), 0, id="pronostica-X-gana-local"),
        pytest.param((0, 1), (1, 1), 0, id="pronostica-2-acaba-en-empate"),
        pytest.param((2, 1), (2, 3), 0, id="acierta-goles-local-pero-no-signo"),
    ],
)
def test_puntuar(pronostico, resultado, esperado):
    assert puntuar(pronostico, resultado) == esperado
