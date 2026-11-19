from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    """Configuración del worker, leída de variables con prefijo PORRA_."""

    model_config = SettingsConfigDict(env_prefix="PORRA_")

    database_url: str
    redis_url: str
