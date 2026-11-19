from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    """Configuración de la cola de tareas, leída de variables con prefijo PORRA_."""

    model_config = SettingsConfigDict(env_prefix="PORRA_")

    redis_url: str
