import numpy as np
import pandas as pd
import pytest

from porra_predictor.modelo import ajustar, matriz_marcadores, mejor_pronostico, puntos_esperados


def test_la_matriz_suma_casi_uno():
    assert matriz_marcadores(1.5, 1.1).sum() == pytest.approx(1.0, abs=1e-3)


def test_puntos_esperados_de_una_matriz_pequena():
    # Filas: goles del local (0, 1). Columnas: goles del visitante (0, 1).
    matriz = np.array([[0.4, 0.1], [0.3, 0.2]])
    # P(gana local) = 0.3, P(empate) = 0.4 + 0.2 = 0.6, P(gana visitante) = 0.1
    esperados = puntos_esperados(matriz)
    assert esperados[0, 0] == pytest.approx(0.6 + 2 * 0.4)
    assert esperados[1, 0] == pytest.approx(0.3 + 2 * 0.3)
    assert esperados[0, 1] == pytest.approx(0.1 + 2 * 0.1)
    assert mejor_pronostico(matriz) == (0, 0)


def test_con_un_local_muy_favorito_pronostica_su_victoria():
    local, visitante = mejor_pronostico(matriz_marcadores(3.0, 0.3))
    assert local > visitante


def test_ajustar_calcula_las_fuerzas_relativas():
    partidos = pd.DataFrame(
        {
            "local": ["A", "B"],
            "visitante": ["B", "A"],
            "goles_local": [2, 1],
            "goles_visitante": [0, 1],
        }
    )
    modelo = ajustar(partidos)
    # Medias: 1.5 en casa y 0.5 fuera. A marca 2 en casa (ataque 2/1.5);
    # B encaja 2 fuera (defensa 2/1.5). λ del local = 1.5 · 4/3 · 4/3.
    lambda_local, _ = modelo.lambdas("A", "B")
    assert lambda_local == pytest.approx(1.5 * 4 / 3 * 4 / 3)


def test_un_equipo_sin_historia_cuenta_como_uno_medio():
    partidos = pd.DataFrame(
        {"local": ["A"], "visitante": ["B"], "goles_local": [1], "goles_visitante": [1]}
    )
    assert ajustar(partidos).lambdas("Nuevo", "Recien") == pytest.approx((1.0, 1.0))
