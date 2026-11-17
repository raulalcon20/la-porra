from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


def crear_sesiones(database_url: str) -> sessionmaker[Session]:
    """Fábrica de sesiones conectadas a la base de datos."""
    engine = create_engine(database_url)
    return sessionmaker(engine)
