import argparse

from porra_api.worker.cola import encolar_puntuaciones, obtener_cola
from porra_api.worker.config import WorkerSettings


def main() -> None:
    parser = argparse.ArgumentParser(description="Encola la puntuación de una o varias jornadas")
    parser.add_argument("jornadas", type=int, nargs="+", help="Ids de jornada")
    args = parser.parse_args()

    encolar_puntuaciones(obtener_cola(WorkerSettings().redis_url), args.jornadas)
    print(f"Encoladas las jornadas {args.jornadas}")


if __name__ == "__main__":
    main()
