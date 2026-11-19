import numpy as np
import pandas as pd
import pytest

from porra_predictor.modelo import (
    _pesos,
    ajustar,
    matriz_marcadores,
    mejor_pronostico,
    puntos_esperados,
)


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


def test_un_partido_de_hace_una_vida_media_pesa_la_mitad():
    referencia = pd.Timestamp("2026-01-01")
    fechas = pd.Series(pd.to_datetime(["2026-01-01", "2025-07-05", "2025-01-06"]))
    pesos = _pesos(fechas, referencia, vida_media_dias=180)
    assert list(pesos) == pytest.approx([1.0, 0.5, 0.25])


def test_la_ponderacion_da_mas_peso_a_lo_reciente():
    partidos = pd.DataFrame(
        {
            "fecha": pd.to_datetime(["2024-01-01", "2025-01-01", "2024-01-01", "2025-01-01"]),
            "local": ["A", "A", "B", "B"],
            "visitante": ["B", "B", "A", "A"],
            "goles_local": [0, 3, 1, 1],
            "goles_visitante": [0, 0, 1, 1],
        }
    )
    referencia = pd.Timestamp("2025-01-02")
    sin_pesos = ajustar(partidos).ataque_casa["A"]
    con_pesos = ajustar(partidos, referencia=referencia, vida_media_dias=30).ataque_casa["A"]
    # A marcó 0 hace un año y 3 hace un día: con pesos, cuenta casi solo el 3.
    assert con_pesos > sin_pesos


def test_los_equipos_nuevos_usan_la_media_de_los_ascendidos():
    partidos = pd.DataFrame(
        {
            "temporada": ["2324", "2324", "2425", "2425"],
            "local": ["A", "B", "A", "C"],
            "visitante": ["B", "A", "C", "A"],
            "goles_local": [2, 1, 3, 0],
            "goles_visitante": [1, 1, 0, 2],
        }
    )
    modelo = ajustar(partidos, ascendidos=True)
    # C asciende en 2425: en casa marca 0 y encaja 2; fuera marca 0 y encaja 3.
    # Medias: 1.5 en casa y 1.0 fuera. Un equipo nuevo hereda esas fuerzas:
    # λ(A en casa contra un nuevo) = 1.5 · (2.5 / 1.5) · (3 / 1.5) = 5.0
    # λ(el nuevo fuera) = 1.0 · (0 / 1.0) · ... = 0.0
    assert modelo.lambdas("A", "Nuevo") == pytest.approx((5.0, 0.0))
