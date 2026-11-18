from datetime import datetime, timedelta
from enum import StrEnum

APERTURA_PRONOSTICOS = timedelta(days=7)


class Ventana(StrEnum):
    NO_ABIERTA = "no_abierta"
    ABIERTA = "abierta"
    CERRADA = "cerrada"


def ventana_pronosticos(inicio: datetime, ahora: datetime) -> Ventana:
    """Si en el instante `ahora` se puede pronosticar un partido que empieza en `inicio`."""
    if ahora >= inicio:
        return Ventana.CERRADA
    if ahora < inicio - APERTURA_PRONOSTICOS:
        return Ventana.NO_ABIERTA
    return Ventana.ABIERTA
