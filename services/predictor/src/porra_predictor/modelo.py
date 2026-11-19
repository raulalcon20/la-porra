from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.stats import poisson

from porra_predictor.puntos import PUNTOS_EXACTO, PUNTOS_SIGNO

MAX_GOLES = 8


@dataclass(frozen=True)
class Modelo:
    """Fuerzas de cada equipo relativas a la media de la liga (1.0 = equipo medio)."""

    media_local: float
    media_visitante: float
    ataque_casa: dict[str, float]
    defensa_casa: dict[str, float]
    ataque_fuera: dict[str, float]
    defensa_fuera: dict[str, float]

    def lambdas(self, local: str, visitante: str) -> tuple[float, float]:
        """Goles esperados de cada equipo. Un equipo sin historia cuenta como uno medio."""
        lambda_local = (
            self.media_local
            * self.ataque_casa.get(local, 1.0)
            * self.defensa_fuera.get(visitante, 1.0)
        )
        lambda_visitante = (
            self.media_visitante
            * self.ataque_fuera.get(visitante, 1.0)
            * self.defensa_casa.get(local, 1.0)
        )
        return lambda_local, lambda_visitante


def ajustar(partidos: pd.DataFrame) -> Modelo:
    """Estima las fuerzas de ataque y defensa, en casa y fuera, a partir de partidos jugados."""
    media_local = partidos["goles_local"].mean()
    media_visitante = partidos["goles_visitante"].mean()
    en_casa = partidos.groupby("local")
    fuera = partidos.groupby("visitante")
    return Modelo(
        media_local=media_local,
        media_visitante=media_visitante,
        ataque_casa=(en_casa["goles_local"].mean() / media_local).to_dict(),
        defensa_casa=(en_casa["goles_visitante"].mean() / media_visitante).to_dict(),
        ataque_fuera=(fuera["goles_visitante"].mean() / media_visitante).to_dict(),
        defensa_fuera=(fuera["goles_local"].mean() / media_local).to_dict(),
    )


def matriz_marcadores(
    lambda_local: float, lambda_visitante: float, max_goles: int = MAX_GOLES
) -> np.ndarray:
    """Probabilidad de cada marcador: la fila es el gol del local y la columna, el del visitante."""
    goles = np.arange(max_goles + 1)
    return np.outer(poisson.pmf(goles, lambda_local), poisson.pmf(goles, lambda_visitante))


def puntos_esperados(matriz: np.ndarray) -> np.ndarray:
    """Puntos esperados de pronosticar cada marcador: P(signo) + 2 · P(exacto)."""
    p_local = np.tril(matriz, -1).sum()
    p_empate = np.trace(matriz)
    p_visitante = np.triu(matriz, 1).sum()
    filas, columnas = np.indices(matriz.shape)
    p_signo = np.where(
        filas > columnas, p_local, np.where(filas == columnas, p_empate, p_visitante)
    )
    return PUNTOS_SIGNO * p_signo + (PUNTOS_EXACTO - PUNTOS_SIGNO) * matriz


def mejor_pronostico(matriz: np.ndarray) -> tuple[int, int]:
    """El marcador que maximiza los puntos esperados (no tiene por qué ser el más probable)."""
    esperados = puntos_esperados(matriz)
    fila, columna = np.unravel_index(np.argmax(esperados), esperados.shape)
    return int(fila), int(columna)
