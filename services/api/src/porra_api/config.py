from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración de la API, leída de variables de entorno con prefijo PORRA_."""

    model_config = SettingsConfigDict(env_prefix="PORRA_")

    app_version: str = "0.1.0"
    environment: str = "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
