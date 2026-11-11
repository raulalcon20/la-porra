import pytest

from porra_api.config import get_settings


@pytest.fixture(autouse=True)
def entorno_de_test(monkeypatch):
    """Configuración mínima para todos los tests, con la caché de settings limpia."""
    monkeypatch.setenv("PORRA_DATABASE_URL", "postgresql+psycopg://test:test@localhost:5432/test")
    monkeypatch.delenv("PORRA_ENVIRONMENT", raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
