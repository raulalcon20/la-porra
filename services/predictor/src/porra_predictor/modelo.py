from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.stats import poisson

from porra_predictor.puntos import PUNTOS_EXACTO, PUNTOS_SIGNO

MAX_GOLES = 8


@dataclass(frozen=True)
class Modelo:
    """Fuerzas de cada equipo relativas a la media de la liga (1.0 = equipo medio).

    Las fuerzas `*_nuevo` se usan para los equipos sin historia (recién ascendidos).
    """

    media_local: float
    media_visitante: float
    ataque_casa: dict[str, float]
    defensa_casa: dict[str, float]
    ataque_fuera: dict[str, float]
    defensa_fuera: dict[str, float]
    ataque_casa_nuevo: float = 1.0
    defensa_casa_nuevo: float = 1.0
    ataque_fuera_nuevo: float = 1.0
    defensa_fuera_nuevo: float = 1.0

    def lambdas(self, local: str, visitante: str) -> tuple[float, float]:
        """Goles esperados de cada equipo."""
        lambda_local = (
            self.media_local
            * self.ataque_casa.get(local, self.ataque_casa_nuevo)
            * self.defensa_fuera.get(visitante, self.defensa_fuera_nuevo)
        )
        lambda_visitante = (
            self.media_visitante
            * self.ataque_fuera.get(visitante, self.ataque_fuera_nuevo)
            * self.defensa_casa.get(local, self.defensa_casa_nuevo)
        )
        return lambda_local, lambda_visitante


def _pesos(fechas: pd.Series, referencia: pd.Timestamp, vida_media_dias: float) -> pd.Series:
    """Un partido de hace `vida_media_dias` pesa la mitad que uno de la fecha de referencia."""
    dias = (referencia - fechas).dt.days
    return 0.5 ** (dias / vida_media_dias)


def _media(partidos: pd.DataFrame, columna: str) -> float:
    """Media ponderada por la columna `peso`."""
    return float((partidos[columna] * partidos["peso"]).sum() / partidos["peso"].sum())


def _media_por_equipo(partidos: pd.DataFrame, equipo: str, columna: str) -> pd.Series:
    """Media ponderada de `columna` para cada valor de la columna `equipo`."""
    ponderado = (partidos[columna] * partidos["peso"]).groupby(partidos[equipo]).sum()
    return ponderado / partidos["peso"].groupby(partidos[equipo]).sum()


def _ascendidos(partidos: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Partidos en los que el local (o el visitante) no jugó la temporada anterior."""
    equipos = {
        temporada: set(grupo["local"]) | set(grupo["visitante"])
        for temporada, grupo in partidos.groupby("temporada")
    }
    temporadas = sorted(equipos)
    anterior = dict(zip(temporadas[1:], temporadas[:-1], strict=True))

    def es_ascendido(equipo: str, temporada: str) -> bool:
        previa = anterior.get(temporada)
        return previa is not None and equipo not in equipos[previa]

    def mascara(columna: str) -> pd.Series:
        valores = [
            es_ascendido(equipo, temporada)
            for equipo, temporada in zip(partidos[columna], partidos["temporada"], strict=True)
        ]
        return pd.Series(valores, index=partidos.index)

    return mascara("local"), mascara("visitante")


def ajustar(
    partidos: pd.DataFrame,
    referencia: pd.Timestamp | None = None,
    vida_media_dias: float | None = None,
    ascendidos: bool = False,
) -> Modelo:
    """Estima las fuerzas de ataque y defensa, en casa y fuera, a partir de partidos jugados.

    - `vida_media_dias`: si se indica, los partidos antiguos pesan menos (necesita `referencia`).
    - `ascendidos`: si es True, los equipos sin historia usan la media de los ascendidos anteriores.
    """
    if vida_media_dias is None:
        partidos = partidos.assign(peso=1.0)
    else:
        if referencia is None:
            raise ValueError("La ponderación temporal necesita una fecha de referencia")
        partidos = partidos.assign(peso=_pesos(partidos["fecha"], referencia, vida_media_dias))

    media_local = _media(partidos, "goles_local")
    media_visitante = _media(partidos, "goles_visitante")

    nuevos: dict[str, float] = {}
    if ascendidos:
        local_ascendido, visitante_ascendido = _ascendidos(partidos)
        if local_ascendido.any() and visitante_ascendido.any():
            en_casa = partidos[local_ascendido]
            fuera = partidos[visitante_ascendido]
            nuevos = {
                "ataque_casa_nuevo": _media(en_casa, "goles_local") / media_local,
                "defensa_casa_nuevo": _media(en_casa, "goles_visitante") / media_visitante,
                "ataque_fuera_nuevo": _media(fuera, "goles_visitante") / media_visitante,
                "defensa_fuera_nuevo": _media(fuera, "goles_local") / media_local,
            }

    return Modelo(
        media_local=media_local,
        media_visitante=media_visitante,
        ataque_casa=(_media_por_equipo(partidos, "local", "goles_local") / media_local).to_dict(),
        defensa_casa=(
            _media_por_equipo(partidos, "local", "goles_visitante") / media_visitante
        ).to_dict(),
        ataque_fuera=(
            _media_por_equipo(partidos, "visitante", "goles_visitante") / media_visitante
        ).to_dict(),
        defensa_fuera=(
            _media_por_equipo(partidos, "visitante", "goles_local") / media_local
        ).to_dict(),
        **nuevos,
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
