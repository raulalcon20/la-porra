# Nombre en la API (football-data.org) → nombre en los CSV de football-data.co.uk.
EQUIVALENCIAS = {
    "Alavés": "Alaves",
    "Athletic": "Ath Bilbao",
    "Atleti": "Ath Madrid",
    "Barça": "Barcelona",
    "Celta": "Celta",
    "Deportivo": "La Coruna",
    "Elche": "Elche",
    "Espanyol": "Espanol",
    "Getafe": "Getafe",
    "Levante": "Levante",
    "Málaga": "Malaga",
    "Osasuna": "Osasuna",
    "Rayo Vallecano": "Vallecano",
    "Real Betis": "Betis",
    "Real Madrid": "Real Madrid",
    "Real Sociedad": "Sociedad",
    "Santander": "Santander",
    "Sevilla FC": "Sevilla",
    "Valencia": "Valencia",
    "Villarreal": "Villarreal",
}


class EquipoDesconocido(Exception):
    """Un equipo de la API que no está en la tabla de equivalencias."""


def nombre_en_modelo(nombre_api: str) -> str:
    try:
        return EQUIVALENCIAS[nombre_api]
    except KeyError:
        raise EquipoDesconocido(
            f"El equipo {nombre_api!r} no está en EQUIVALENCIAS (porra_predictor/equipos.py)"
        ) from None
