import httpx


class ClienteAPI:
    """Cliente de la API de La Porra, autenticado como La Máquina."""

    def __init__(self, base_url: str, token: str, transport: httpx.BaseTransport | None = None):
        self._http = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
            transport=transport,
        )

    def partidos(self, temporada: int, jornada: int) -> list[dict]:
        respuesta = self._http.get("/partidos", params={"temporada": temporada, "jornada": jornada})
        respuesta.raise_for_status()
        return respuesta.json()

    def pronosticar(self, partido_id: int, goles_local: int, goles_visitante: int) -> bool:
        """Envía el pronóstico. Devuelve False si el partido está fuera de plazo (409)."""
        respuesta = self._http.put(
            f"/pronosticos/{partido_id}",
            json={"goles_local": goles_local, "goles_visitante": goles_visitante},
        )
        if respuesta.status_code == 409:
            return False
        respuesta.raise_for_status()
        return True
