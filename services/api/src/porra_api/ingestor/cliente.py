import logging
import time
from collections.abc import Callable

import httpx

log = logging.getLogger(__name__)


class ClienteFootballData:
    """Cliente de la API de football-data.org que respeta su límite de peticiones."""

    def __init__(
        self,
        token: str,
        base_url: str,
        transport: httpx.BaseTransport | None = None,
        dormir: Callable[[float], None] = time.sleep,
        max_intentos: int = 4,
    ) -> None:
        self._http = httpx.Client(
            base_url=base_url,
            headers={"X-Auth-Token": token},
            timeout=10.0,
            transport=transport,
        )
        self._dormir = dormir
        self._max_intentos = max_intentos

    def get(self, ruta: str, params: dict | None = None) -> dict:
        """GET con reintentos: 429 → espera lo que diga el servidor; 5xx/red → backoff."""
        for intento in range(1, self._max_intentos + 1):
            try:
                respuesta = self._http.get(ruta, params=params)
            except httpx.TransportError as error:
                log.warning("Error de red (intento %d): %s", intento, error)
                self._dormir(2**intento)
                continue

            if respuesta.status_code == 429:
                espera = int(respuesta.headers.get("X-RequestCounter-Reset", "60"))
                log.warning("Límite alcanzado (429). Esperando %d s", espera)
                self._dormir(espera)
                continue

            if respuesta.status_code >= 500:
                log.warning("Error %d del servidor (intento %d)", respuesta.status_code, intento)
                self._dormir(2**intento)
                continue

            respuesta.raise_for_status()
            self._respetar_limite(respuesta)
            return respuesta.json()

        raise RuntimeError(f"Sin respuesta válida de {ruta} tras {self._max_intentos} intentos")

    def _respetar_limite(self, respuesta: httpx.Response) -> None:
        """Si no quedan peticiones en el minuto, espera a que se reinicie el contador."""
        disponibles = int(
            respuesta.headers.get("X-Requests-Available-Minute", "1")
        )  # Sin cabecera, asumimos que hay disponibles
        if disponibles <= 0:
            espera = int(respuesta.headers.get("X-RequestCounter-Reset", "60"))
            log.info("Límite de peticiones en el minuto alcanzado. Esperando %d s", espera)
            self._dormir(espera)

    def partidos(self, competicion: str, temporada: int) -> list[dict]:
        """Todos los partidos de una competición y temporada, en una sola petición."""
        datos = self.get(f"/competitions/{competicion}/matches", params={"season": temporada})
        return datos["matches"]

    def competicion(self, codigo: str) -> dict:
        """Datos de una competición (nombre, tipo...)."""
        return self.get(f"/competitions/{codigo}")
