from pathlib import Path

import pandas as pd

COLUMNAS = {
    "Date": "fecha",
    "HomeTeam": "local",
    "AwayTeam": "visitante",
    "FTHG": "goles_local",
    "FTAG": "goles_visitante",
}


def cargar_temporada(ruta: Path) -> pd.DataFrame:
    """Un CSV de football-data.co.uk, con las columnas renombradas y solo los partidos jugados."""
    df = pd.read_csv(ruta, usecols=list(COLUMNAS), encoding="latin-1")
    df = df.rename(columns=COLUMNAS).dropna(subset=["goles_local", "goles_visitante"])
    df["fecha"] = pd.to_datetime(df["fecha"], dayfirst=True)
    df[["goles_local", "goles_visitante"]] = df[["goles_local", "goles_visitante"]].astype(int)
    df["temporada"] = ruta.stem.split("_")[1]
    return df


def cargar_partidos(carpeta: Path) -> pd.DataFrame:
    """Todas las temporadas de la carpeta, en un único DataFrame ordenado por fecha."""
    archivos = sorted(carpeta.glob("SP1_*.csv"))
    if not archivos:
        raise FileNotFoundError(f"No hay ningún CSV SP1_*.csv en {carpeta}")
    partidos = pd.concat([cargar_temporada(a) for a in archivos], ignore_index=True)
    return partidos.sort_values("fecha", ignore_index=True)
