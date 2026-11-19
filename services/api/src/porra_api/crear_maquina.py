import argparse

from sqlalchemy import select

from porra_api.config import get_settings
from porra_api.db import crear_sesiones
from porra_api.models import Jugador
from porra_api.seguridad import generar_token, hash_token


def main() -> None:
    parser = argparse.ArgumentParser(description="Crea a La Máquina y muestra su token una vez")
    parser.add_argument("--nombre", default="La Máquina")
    args = parser.parse_args()

    Sesion = crear_sesiones(get_settings().database_url)
    with Sesion.begin() as sesion:
        if sesion.scalar(select(Jugador).where(Jugador.es_maquina)) is not None:
            raise SystemExit("La Máquina ya existe: no se crea otra")
        token = generar_token()
        sesion.add(Jugador(nombre=args.nombre, es_maquina=True, token_hash=hash_token(token)))

    print(f"Creado el jugador {args.nombre!r}. Su token, que no se volverá a mostrar:")
    print(token)


if __name__ == "__main__":
    main()
