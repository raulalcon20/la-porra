from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    MetaData,
    String,
    UniqueConstraint,
    false,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Nombres predecibles para índices y restricciones (los necesita Alembic)
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Competicion(Base):
    __tablename__ = "competiciones"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(10), unique=True)
    nombre: Mapped[str] = mapped_column(String(100))
    tipo: Mapped[str] = mapped_column(String(20))


class Jornada(Base):
    __tablename__ = "jornadas"
    __table_args__ = (
        UniqueConstraint(
            "competicion_id",
            "temporada",
            "fase",
            "numero",
            postgresql_nulls_not_distinct=True,
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    competicion_id: Mapped[int] = mapped_column(ForeignKey("competiciones.id", ondelete="RESTRICT"))
    temporada: Mapped[int]
    fase: Mapped[str] = mapped_column(String(30))
    numero: Mapped[int | None]


class Partido(Base):
    __tablename__ = "partidos"

    id: Mapped[int] = mapped_column(primary_key=True)
    football_data_id: Mapped[int] = mapped_column(unique=True)
    jornada_id: Mapped[int] = mapped_column(ForeignKey("jornadas.id", ondelete="RESTRICT"))
    equipo_local: Mapped[str | None] = mapped_column(String(100))
    equipo_visitante: Mapped[str | None] = mapped_column(String(100))
    inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    estado: Mapped[str] = mapped_column(String(20))
    goles_local: Mapped[int | None]
    goles_visitante: Mapped[int | None]


class Jugador(Base):
    __tablename__ = "jugadores"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50), unique=True)
    es_maquina: Mapped[bool] = mapped_column(server_default=false())
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Porra(Base):
    __tablename__ = "porras"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    competicion_id: Mapped[int] = mapped_column(ForeignKey("competiciones.id", ondelete="RESTRICT"))
    temporada: Mapped[int]
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Miembro(Base):
    __tablename__ = "miembros"

    porra_id: Mapped[int] = mapped_column(
        ForeignKey("porras.id", ondelete="CASCADE"), primary_key=True
    )
    jugador_id: Mapped[int] = mapped_column(
        ForeignKey("jugadores.id", ondelete="CASCADE"), primary_key=True
    )


class Pronostico(Base):
    __tablename__ = "pronosticos"
    __table_args__ = (UniqueConstraint("jugador_id", "partido_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    jugador_id: Mapped[int] = mapped_column(ForeignKey("jugadores.id", ondelete="CASCADE"))
    partido_id: Mapped[int] = mapped_column(ForeignKey("partidos.id", ondelete="RESTRICT"))
    goles_local: Mapped[int]
    goles_visitante: Mapped[int]
    puntos: Mapped[int | None]
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
