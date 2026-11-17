from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class IngestorSettings(BaseSettings):
    """Configuración del ingestor, leída de variables de entorno con prefijo PORRA_."""

    model_config = SettingsConfigDict(env_prefix="PORRA_")

    database_url: str
    football_data_token: SecretStr
    football_data_url: str = "https://api.football-data.org/v4"
