import argparse

from sqlalchemy import select

from porra_api.config import get_settings
from porra_api.db import crear_sesiones
from porra_api.models import Jugador
from porra_api.seguridad import generar_token, hash_token


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Genera un token nuevo para un jugador; el anterior deja de valer"
    )
    parser.add_argument("nombre")
    args = parser.parse_args()

    Sesion = crear_sesiones(get_settings().database_url)
    with Sesion.begin() as sesion:
        jugador = sesion.scalar(select(Jugador).where(Jugador.nombre == args.nombre))
        if jugador is None:
            raise SystemExit(f"No existe ningún jugador llamado {args.nombre!r}")
        token = generar_token()
        jugador.token_hash = hash_token(token)

    print(f"Nuevo token de {args.nombre!r}, que no se volverá a mostrar:")
    print(token)


if __name__ == "__main__":
    main()
