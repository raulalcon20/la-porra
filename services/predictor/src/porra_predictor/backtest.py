from pathlib import Path

import pandas as pd

from porra_predictor.datos import cargar_partidos
from porra_predictor.modelo import ajustar, matriz_marcadores, mejor_pronostico
from porra_predictor.puntos import PUNTOS_EXACTO, puntuar

CARPETA_DATOS = Path(__file__).resolve().parents[2] / "datos"
VENTANA = pd.Timedelta(days=730)
TEMPORADAS_EVALUADAS = ["2425", "2526"]
VIDA_MEDIA_DIAS = 180  # Fijada antes de ver los resultados, para no sobreajustar.
VARIANTES = {
    "Base": {},
    "+ ascendidos": {"ascendidos": True},
    "+ ponderación": {"vida_media_dias": VIDA_MEDIA_DIAS},
    "+ las dos": {"ascendidos": True, "vida_media_dias": VIDA_MEDIA_DIAS},
}
BASELINES = {"Siempre 1-0": (1, 0), "Siempre 2-1": (2, 1)}


def pronosticos_maquina(
    partidos: pd.DataFrame, temporada: str, **opciones
) -> list[tuple[int, int]]:
    """Walk-forward: cada día se pronostica con un modelo entrenado solo con partidos anteriores."""
    evaluados = partidos[partidos["temporada"] == temporada]
    pronosticos: dict[int, tuple[int, int]] = {}
    for fecha, del_dia in evaluados.groupby("fecha"):
        historia = partidos[(partidos["fecha"] < fecha) & (partidos["fecha"] >= fecha - VENTANA)]
        modelo = ajustar(historia, referencia=fecha, **opciones)
        for indice, partido in del_dia.iterrows():
            lambdas = modelo.lambdas(partido["local"], partido["visitante"])
            pronosticos[indice] = mejor_pronostico(matriz_marcadores(*lambdas))
    return [pronosticos[indice] for indice in evaluados.index]


def resumen(nombre: str, pronosticos: list, resultados: list) -> None:
    puntos = [puntuar(p, r) for p, r in zip(pronosticos, resultados, strict=True)]
    exactos = sum(punto == PUNTOS_EXACTO for punto in puntos) / len(puntos)
    print(
        f"  {nombre:<14} {sum(puntos) / len(puntos):.3f} pts/partido  {sum(puntos):4d} pts  "
        f"exactos {exactos:.1%}"
    )


def main() -> None:
    partidos = cargar_partidos(CARPETA_DATOS)
    for temporada in TEMPORADAS_EVALUADAS:
        evaluados = partidos[partidos["temporada"] == temporada]
        resultados = list(zip(evaluados["goles_local"], evaluados["goles_visitante"], strict=True))

        print(f"\nTemporada {temporada} ({len(evaluados)} partidos)")
        for nombre, opciones in VARIANTES.items():
            resumen(nombre, pronosticos_maquina(partidos, temporada, **opciones), resultados)
        for nombre, marcador in BASELINES.items():
            resumen(nombre, [marcador] * len(resultados), resultados)


if __name__ == "__main__":
    main()
