PUNTOS_EXACTO = 3
PUNTOS_SIGNO = 1


def _signo(goles_local: int, goles_visitante: int) -> str:
    """Signo de la quiniela: '1' gana el local, 'X' empate, '2' gana el visitante."""
    if goles_local > goles_visitante:
        return "1"
    if goles_local < goles_visitante:
        return "2"
    return "X"


def puntuar(pronostico: tuple[int, int], resultado: tuple[int, int]) -> int:
    """Puntos de un pronóstico (goles local, goles visitante) frente al resultado real."""
    if pronostico == resultado:
        return PUNTOS_EXACTO
    if _signo(*pronostico) == _signo(*resultado):
        return PUNTOS_SIGNO
    return 0
