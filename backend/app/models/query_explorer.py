from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue

from app.models.analytics import GraphData, Subject, Year


class NoQueryParameters(BaseModel):
    model_config = ConfigDict(extra='forbid')


class NeoQueryParameters(BaseModel):
    model_config = ConfigDict(extra='forbid')
    anio: Year | None = None
    desde: Year | None = None
    hasta: Year | None = None
    materia: Subject | None = None
    aprobado: bool | None = None
    carrera_id: str | None = Field(default=None, pattern=r'^carrera:[0-9a-f]{64}$')
    cohorte_id: str | None = Field(default=None, pattern=r'^(201[5-9]|202[0-4]):[0-9a-f]{20,32}$', max_length=37)


class QueryDescription(BaseModel):
    id: int
    titulo: str
    objetivo: str
    explicacion: str
    parametros: list[str]
    valores_defecto: dict[str, JsonValue]
    visualizacion: str


class QueryCatalog(BaseModel):
    mongodb: list[QueryDescription]
    neo4j: list[QueryDescription]


class QueryExecution(BaseModel):
    id: int
    titulo: str
    resultado: JsonValue
    filas: int
    segundos: float
    grafo: GraphData | None = None


class QueryCatalogResponse(BaseModel):
    status: Literal['ok'] = 'ok'
    data: QueryCatalog
    meta: dict[str, JsonValue]
