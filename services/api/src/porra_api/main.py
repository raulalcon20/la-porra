from contextlib import asynccontextmanager

from fastapi import FastAPI

from porra_api.config import get_settings
from porra_api.rutas import competiciones, jugadores, partidos, porras, pronosticos


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_settings()  # Fail fast: si la configuración es inválida, la API no arranca.
    yield


app = FastAPI(title="La Porra API", lifespan=lifespan)
app.include_router(competiciones.router)
app.include_router(jugadores.router)
app.include_router(partidos.router)
app.include_router(porras.router)
app.include_router(pronosticos.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/version")
def version() -> dict[str, str]:
    settings = get_settings()
    return {"version": settings.app_version, "environment": settings.environment}
