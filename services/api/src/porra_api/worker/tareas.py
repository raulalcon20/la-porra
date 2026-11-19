import os
import socket
import time


def tarea_lenta(numero: int, segundos: float = 2.0) -> str:
    """Tarea de prueba: simula trabajo y dice qué worker la ha hecho."""
    time.sleep(segundos)
    return f"tarea {numero:>2} → {socket.gethostname()} (pid {os.getpid()})"
