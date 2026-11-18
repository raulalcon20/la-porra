from dataclasses import dataclass


@dataclass(frozen=True)
class FilaClasificacion:
    nombre: str
    es_maquina: bool
    puntos: int
    exactos: int


def _criterio(fila: FilaClasificacion) -> tuple[int, int]:
    """Lo que decide la posición: puntos y, en caso de empate, resultados exactos."""
    return (fila.puntos, fila.exactos)


def con_posiciones(filas: list[FilaClasificacion]) -> list[tuple[int, FilaClasificacion]]:
    """Ordena la clasificación y numera las posiciones.

    Quien empata en puntos y exactos comparte posición, y el siguiente salta
    los puestos compartidos (ranking de competición: 1, 2, 2, 4).
    """
    ordenadas = sorted(filas, key=lambda f: (-f.puntos, -f.exactos, f.nombre.lower()))
    resultado: list[tuple[int, FilaClasificacion]] = []
    for indice, fila in enumerate(ordenadas, start=1):
        if resultado and _criterio(fila) == _criterio(resultado[-1][1]):
            posicion = resultado[-1][0]
        else:
            posicion = indice
        resultado.append((posicion, fila))
    return resultado
