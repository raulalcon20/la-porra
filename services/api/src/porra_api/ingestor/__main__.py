import argparse
import logging

from porra_api.db import crear_sesiones
from porra_api.ingestor.cliente import ClienteFootballData
from porra_api.ingestor.config import IngestorSettings
from porra_api.ingestor.guardar import guardar_competicion, guardar_temporada
from porra_api.ingestor.transformar import transformar_partido
from porra_api.worker.cola import encolar_puntuaciones, obtener_cola
from porra_api.worker.puntuar import jornadas_por_puntuar

log = logging.getLogger("porra_api.ingestor")


def main() -> None:
    parser = argparse.ArgumentParser(description="Descarga partidos de football-data.org")
    parser.add_argument("--competicion", default="PD", help="Código de la competición (PD, CL...)")
    parser.add_argument("--temporada", type=int, help="Año de inicio; por defecto, la actual")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    settings = IngestorSettings()
    cliente = ClienteFootballData(
        token=settings.football_data_token.get_secret_value(),
        base_url=settings.football_data_url,
    )

    info = cliente.competicion(args.competicion)
    temporada = args.temporada or int(info["currentSeason"]["startDate"][:4])
    partidos = [transformar_partido(dato) for dato in cliente.partidos(args.competicion, temporada)]

    Sesion = crear_sesiones(settings.database_url)
    with Sesion.begin() as sesion:
        competicion_id = guardar_competicion(sesion, info["code"], info["name"], info["type"])
        guardados = guardar_temporada(sesion, competicion_id, partidos)
    log.info("Guardados %d partidos de %s %d", guardados, args.competicion, temporada)

    # Solo después del COMMIT: así el worker siempre lee los resultados nuevos.
    with Sesion() as sesion:
        pendientes = jornadas_por_puntuar(sesion)
    encolar_puntuaciones(obtener_cola(settings.redis_url), pendientes)
    log.info("Encoladas %d jornadas para puntuar: %s", len(pendientes), pendientes)


if __name__ == "__main__":
    main()
