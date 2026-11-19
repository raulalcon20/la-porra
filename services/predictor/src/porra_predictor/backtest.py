from pathlib import Path

import pandas as pd

from porra_predictor.datos import cargar_partidos
from porra_predictor.modelo import ajustar, matriz_marcadores, mejor_pronostico
from porra_predictor.puntos import PUNTOS_EXACTO, puntuar

CARPETA_DATOS = Path(__file__).resolve().parents[2] / "datos"
VENTANA = pd.Timedelta(days=730)
TEMPORADAS_EVALUADAS = ["2425", "2526"]
BASELINES = {"Siempre 1-1": (1, 1), "Siempre 1-0": (1, 0), "Siempre 2-1": (2, 1)}


def pronosticos_maquina(partidos: pd.DataFrame, temporada: str) -> list[tuple[int, int]]:
    """Walk-forward: cada día se pronostica con un modelo entrenado solo con partidos anteriores."""
    evaluados = partidos[partidos["temporada"] == temporada]
    pronosticos: dict[int, tuple[int, int]] = {}
    for fecha, del_dia in evaluados.groupby("fecha"):
        historia = partidos[(partidos["fecha"] < fecha) & (partidos["fecha"] >= fecha - VENTANA)]
        modelo = ajustar(historia)
        for indice, partido in del_dia.iterrows():
            lambdas = modelo.lambdas(partido["local"], partido["visitante"])
            pronosticos[indice] = mejor_pronostico(matriz_marcadores(*lambdas))
    return [pronosticos[indice] for indice in evaluados.index]


def resumen(nombre: str, pronosticos: list, resultados: list) -> None:
    puntos = [puntuar(p, r) for p, r in zip(pronosticos, resultados, strict=True)]
    exactos = sum(punto == PUNTOS_EXACTO for punto in puntos) / len(puntos)
    print(
        f"  {nombre:<13} {sum(puntos) / len(puntos):.3f} pts/partido  {sum(puntos):4d} pts  "
        f"exactos {exactos:.1%}"
    )


def main() -> None:
    partidos = cargar_partidos(CARPETA_DATOS)
    for temporada in TEMPORADAS_EVALUADAS:
        evaluados = partidos[partidos["temporada"] == temporada]
        resultados = list(zip(evaluados["goles_local"], evaluados["goles_visitante"], strict=True))
        maquina = pronosticos_maquina(partidos, temporada)

        print(f"\nTemporada {temporada} ({len(evaluados)} partidos)")
        resumen("La Máquina", maquina, resultados)
        for nombre, marcador in BASELINES.items():
            resumen(nombre, [marcador] * len(resultados), resultados)

        marcadores = [f"{local}-{visitante}" for local, visitante in maquina]
        usados = pd.Series(marcadores).value_counts(normalize=True)
        print(
            "  Pronósticos de La Máquina:",
            ", ".join(
                f"{marcador} {proporcion:.0%}" for marcador, proporcion in usados.head(5).items()
            ),
        )


if __name__ == "__main__":
    main()
