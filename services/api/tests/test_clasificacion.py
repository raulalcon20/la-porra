from porra_api.clasificacion import FilaClasificacion, con_posiciones


def fila(nombre, puntos, exactos=0, es_maquina=False):
    return FilaClasificacion(nombre=nombre, es_maquina=es_maquina, puntos=puntos, exactos=exactos)


def posiciones(filas):
    """Simplifica el resultado a pares (posición, nombre), fáciles de comparar."""
    return [(posicion, f.nombre) for posicion, f in con_posiciones(filas)]


def test_sin_jugadores_la_clasificacion_esta_vacia():
    assert con_posiciones([]) == []


def test_ordena_por_puntos():
    filas = [fila("Luis", 4), fila("Ana", 10), fila("Marta", 7)]
    assert posiciones(filas) == [(1, "Ana"), (2, "Marta"), (3, "Luis")]


def test_a_igualdad_de_puntos_desempatan_los_exactos():
    filas = [fila("Ana", 7, exactos=1), fila("Luis", 7, exactos=2)]
    assert posiciones(filas) == [(1, "Luis"), (2, "Ana")]


def test_empate_total_comparte_posicion_y_el_siguiente_salta():
    filas = [
        fila("Pepe", 4),
        fila("Marta", 7, exactos=1),
        fila("Ana", 10),
        fila("Luis", 7, exactos=1),
    ]
    assert posiciones(filas) == [(1, "Ana"), (2, "Luis"), (2, "Marta"), (4, "Pepe")]


def test_dentro_de_un_empate_ordena_por_nombre_sin_importar_mayusculas():
    filas = [fila("beatriz", 5), fila("Alberto", 5)]
    assert posiciones(filas) == [(1, "Alberto"), (1, "beatriz")]


def test_la_maquina_compite_como_una_mas():
    filas = [fila("Ana", 3), fila("La Máquina", 6, exactos=1, es_maquina=True)]
    assert posiciones(filas) == [(1, "La Máquina"), (2, "Ana")]


def test_todos_empatados_al_empezar_la_temporada():
    filas = [fila("Luis", 0), fila("Ana", 0), fila("Marta", 0)]
    assert posiciones(filas) == [(1, "Ana"), (1, "Luis"), (1, "Marta")]
