from pathlib import Path

from porra_predictor.datos import cargar_partidos

CARPETA_DATOS = Path(__file__).resolve().parents[2] / "datos"


def main() -> None:
    partidos = cargar_partidos(CARPETA_DATOS)

    print("Partidos por temporada:")
    print(partidos["temporada"].value_counts().sort_index().to_string(), "\n")

    print(f"Media de goles del local:     {partidos['goles_local'].mean():.2f}")
    print(f"Media de goles del visitante: {partidos['goles_visitante'].mean():.2f}\n")

    diferencia = partidos["goles_local"] - partidos["goles_visitante"]
    print(f"Gana el local:     {(diferencia > 0).mean():.1%}")
    print(f"Empate:            {(diferencia == 0).mean():.1%}")
    print(f"Gana el visitante: {(diferencia < 0).mean():.1%}\n")

    marcadores = partidos["goles_local"].astype(str) + "-" + partidos["goles_visitante"].astype(str)
    print("Los 8 marcadores más frecuentes:")
    print(marcadores.value_counts(normalize=True).head(8).map("{:.1%}".format).to_string())


if __name__ == "__main__":
    main()
