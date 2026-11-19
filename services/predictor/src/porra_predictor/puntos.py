# Deben coincidir con las reglas de la API (porra_api/puntuacion.py).
PUNTOS_EXACTO = 3
PUNTOS_SIGNO = 1


def signo(goles_local: int, goles_visitante: int) -> str:
    if goles_local > goles_visitante:
        return "1"
    if goles_local < goles_visitante:
        return "2"
    return "X"


def puntuar(pronostico: tuple[int, int], resultado: tuple[int, int]) -> int:
    if pronostico == resultado:
        return PUNTOS_EXACTO
    if signo(*pronostico) == signo(*resultado):
        return PUNTOS_SIGNO
    return 0
