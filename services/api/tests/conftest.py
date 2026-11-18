import os
from datetime import UTC, datetime
from itertools import count

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from porra_api.config import get_settings
from porra_api.dependencias import get_sesion
from porra_api.main import app
from porra_api.models import Base, Competicion, Jornada, Partido


@pytest.fixture(autouse=True)
def entorno_de_test(monkeypatch):
    """Configuración mínima para todos los tests, con la caché de settings limpia."""
    monkeypatch.setenv("PORRA_DATABASE_URL", "postgresql+psycopg://test:test@localhost:5432/test")
    monkeypatch.delenv("PORRA_ENVIRONMENT", raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(scope="session")
def engine_test():
    """Engine de la base de datos de pruebas, con las tablas recién creadas."""
    url = os.environ.get("PORRA_TEST_DATABASE_URL")
    if not url:
        pytest.skip("PORRA_TEST_DATABASE_URL no definida: se omiten los tests de base de datos")
    engine = create_engine(url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def sesion(engine_test):
    """Sesión dentro de una transacción que se deshace al terminar el test."""
    with engine_test.connect() as conexion:
        transaccion = conexion.begin()
        sesion = Session(bind=conexion, join_transaction_mode="create_savepoint")
        yield sesion
        sesion.close()
        transaccion.rollback()


@pytest.fixture
def cliente(sesion):
    """TestClient cuya API usa la sesión de pruebas."""
    app.dependency_overrides[get_sesion] = lambda: sesion
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def crear_partido(sesion):
    """Fábrica de partidos de prueba de LaLiga 2026, con su competición y su jornada."""
    competicion = Competicion(codigo="PD", nombre="LaLiga", tipo="LEAGUE")
    sesion.add(competicion)
    sesion.flush()
    jornadas: dict[int, Jornada] = {}
    ids_externos = count(1)

    def _crear(
        jornada: int = 1,
        inicio: datetime = datetime(2026, 12, 6, 20, 0, tzinfo=UTC),
        local: str | None = "Betis",
        visitante: str | None = "Sevilla",
        estado: str = "TIMED",
    ) -> Partido:
        if jornada not in jornadas:
            jornadas[jornada] = Jornada(
                competicion_id=competicion.id, temporada=2026, fase="REGULAR_SEASON", numero=jornada
            )
            sesion.add(jornadas[jornada])
            sesion.flush()
        partido = Partido(
            football_data_id=next(ids_externos),
            jornada_id=jornadas[jornada].id,
            equipo_local=local,
            equipo_visitante=visitante,
            inicio=inicio,
            estado=estado,
        )
        sesion.add(partido)
        sesion.flush()
        return partido

    return _crear
