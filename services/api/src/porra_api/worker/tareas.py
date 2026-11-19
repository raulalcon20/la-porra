import os
import socket
import time
from functools import lru_cache

from sqlalchemy.orm import Session, sessionmaker

from porra_api.db import crear_sesiones
from porra_api.worker.config import WorkerSettings
from porra_api.worker.puntuar import puntuar_jornada


@lru_cache
def _fabrica_sesiones() -> sessionmaker[Session]:
    return crear_sesiones(WorkerSettings().database_url)


def tarea_puntuar_jornada(jornada_id: int) -> int:
    """Tarea de la cola: puntúa una jornada en una única transacción."""
    with _fabrica_sesiones().begin() as sesion:
        return puntuar_jornada(sesion, jornada_id)


def tarea_lenta(numero: int, segundos: float = 2.0) -> str:
    """Tarea de prueba: simula trabajo y dice qué worker la ha hecho."""
    time.sleep(segundos)
    return f"tarea {numero:>2} → {socket.gethostname()} (pid {os.getpid()})"
