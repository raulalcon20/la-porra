from redis import Redis
from rq import Queue, Retry

from porra_api.worker.tareas import tarea_puntuar_jornada

NOMBRE_COLA = "porra"
ESPERAS_REINTENTO = [10, 30, 60]


def obtener_cola(redis_url: str) -> Queue:
    return Queue(NOMBRE_COLA, connection=Redis.from_url(redis_url))


def encolar_puntuaciones(cola: Queue, jornada_ids: list[int]) -> None:
    """Encola la puntuación de cada jornada, con reintentos si falla."""
    for jornada_id in jornada_ids:
        cola.enqueue(
            tarea_puntuar_jornada,
            jornada_id,
            retry=Retry(max=len(ESPERAS_REINTENTO), interval=ESPERAS_REINTENTO),
        )
