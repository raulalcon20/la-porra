import urllib.request
from datetime import date
from pathlib import Path

URL = "https://www.football-data.co.uk/mmz4281/{codigo}/SP1.csv"


def codigos_temporada(hoy: date, cuantas: int) -> list[str]:
    """Códigos de las últimas `cuantas` temporadas, la actual incluida (2026/27 → "2627")."""
    inicio = hoy.year if hoy.month >= 7 else hoy.year - 1
    return [f"{a % 100:02d}{(a + 1) % 100:02d}" for a in range(inicio - cuantas + 1, inicio + 1)]


def descargar(carpeta: Path, codigos: list[str]) -> None:
    """Descarga los CSV de LaLiga de esas temporadas en la carpeta."""
    for codigo in codigos:
        with urllib.request.urlopen(URL.format(codigo=codigo), timeout=30) as respuesta:
            (carpeta / f"SP1_{codigo}.csv").write_bytes(respuesta.read())
