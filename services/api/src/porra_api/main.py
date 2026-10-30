from fastapi import FastAPI

from porra_api.config import get_settings

app = FastAPI(title="La Porra API -API simple")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/version")
def version() -> dict[str, str]:
    settings = get_settings()
    return {"version": settings.app_version, "environment": settings.environment}
