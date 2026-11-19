import argparse
import logging
import tempfile
from datetime import date
from pathlib import Path

import pandas as pd

from porra_predictor.cliente import ClienteAPI
from porra_predictor.config import PredictorSettings
from porra_predictor.datos import cargar_partidos
from porra_predictor.descarga import codigos_temporada, descargar
from porra_predictor.equipos import nombre_en_modelo
from porra_predictor.modelo import Modelo, ajustar, matriz_marcadores, mejor_pronostico

log = logging.getLogger("porra_predictor")
VENTANA = pd.Timedelta(days=730)
TEMPORADAS_A_DESCARGAR = 3
ESTADOS_PENDIENTES = {"SCHEDULED", "TIMED"}


def entrenar(carpeta: Path) -> Modelo:
    """Modelo base con los partidos de los últimos dos años."""
    partidos = cargar_partidos(carpeta)
    hoy = pd.Timestamp(date.today())
    return ajustar(partidos[partidos["fecha"] >= hoy - VENTANA])


def main() -> None:
    parser = argparse.ArgumentParser(description="La Máquina pronostica una jornada por la API")
    parser.add_argument("--temporada", type=int, required=True)
    parser.add_argument("--jornada", type=int, required=True)
    parser.add_argument("--datos", type=Path, help="Carpeta con los CSV; si no, se descargan")
    parser.add_argument("--simular", action="store_true", help="Calcula sin enviar nada")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    settings = PredictorSettings()
    cliente = ClienteAPI(settings.api_url, settings.maquina_token.get_secret_value())

    partidos = [
        p
        for p in cliente.partidos(args.temporada, args.jornada)
        if p["estado"] in ESTADOS_PENDIENTES and p["equipo_local"] and p["equipo_visitante"]
    ]
    # Fail fast: si falta algún equipo en la tabla, no se envía ningún pronóstico.
    equipos = {
        p["id"]: (nombre_en_modelo(p["equipo_local"]), nombre_en_modelo(p["equipo_visitante"]))
        for p in partidos
    }

    if args.datos:
        modelo = entrenar(args.datos)
    else:
        with tempfile.TemporaryDirectory() as carpeta:
            descargar(Path(carpeta), codigos_temporada(date.today(), TEMPORADAS_A_DESCARGAR))
            modelo = entrenar(Path(carpeta))

    for partido in partidos:
        lambdas = modelo.lambdas(*equipos[partido["id"]])
        local, visitante = mejor_pronostico(matriz_marcadores(*lambdas))
        texto = f"{partido['equipo_local']} {local}-{visitante} {partido['equipo_visitante']}"
        if args.simular:
            log.info("(simulado) %s", texto)
        elif cliente.pronosticar(partido["id"], local, visitante):
            log.info("Pronosticado: %s", texto)
        else:
            log.warning("Fuera de plazo: %s", texto)


if __name__ == "__main__":
    main()
