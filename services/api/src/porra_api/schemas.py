from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Nombre = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=50)]
NombrePorra = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=100)]
Goles = Annotated[int, Field(ge=0, le=20)]


class CompeticionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    codigo: str
    nombre: str
    tipo: str


class JugadorCrear(BaseModel):
    nombre: Nombre


class JugadorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    es_maquina: bool


class JugadorCreado(JugadorOut):
    token: str


class PartidoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    equipo_local: str | None
    equipo_visitante: str | None
    inicio: datetime
    estado: str
    goles_local: int | None
    goles_visitante: int | None


class PronosticoIn(BaseModel):
    goles_local: Goles
    goles_visitante: Goles


class PronosticoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    partido_id: int
    goles_local: int
    goles_visitante: int
    puntos: int | None


class PorraCrear(BaseModel):
    nombre: NombrePorra
    temporada: int
    competicion: str = "PD"


class UnirsePorra(BaseModel):
    codigo: str


class PorraOut(BaseModel):
    id: int
    nombre: str
    competicion: str
    temporada: int
    codigo_invitacion: str


class FilaClasificacionOut(BaseModel):
    posicion: int
    nombre: str
    es_maquina: bool
    puntos: int
    exactos: int
