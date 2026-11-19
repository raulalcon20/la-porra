import argparse
import time

from porra_api.worker.cola import obtener_cola
from porra_api.worker.config import WorkerSettings
from porra_api.worker.tareas import tarea_lenta


def main() -> None:
    parser = argparse.ArgumentParser(description="Encola tareas de prueba y espera sus resultados")
    parser.add_argument("cuantas", type=int, nargs="?", default=10)
    args = parser.parse_args()

    cola = obtener_cola(WorkerSettings().redis_url)
    inicio = time.monotonic()
    trabajos = [cola.enqueue(tarea_lenta, numero) for numero in range(1, args.cuantas + 1)]
    print(f"Encoladas {len(trabajos)} tareas en {time.monotonic() - inicio:.3f} s")

    while not all(trabajo.is_finished or trabajo.is_failed for trabajo in trabajos):
        time.sleep(0.5)
        for trabajo in trabajos:
            trabajo.refresh()

    for trabajo in trabajos:
        print(trabajo.return_value() if trabajo.is_finished else f"FALLIDA: {trabajo.id}")
    print(f"Total: {time.monotonic() - inicio:.1f} s")


if __name__ == "__main__":
    main()
