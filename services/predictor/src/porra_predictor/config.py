from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class PredictorSettings(BaseSettings):
    """Configuración del predictor, leída de variables con prefijo PORRA_."""

    model_config = SettingsConfigDict(env_prefix="PORRA_")

    api_url: str
    maquina_token: SecretStr
