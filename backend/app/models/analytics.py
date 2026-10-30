from typing import Annotated, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

Year = Annotated[int, Field(ge=2015, le=2024)]
Subject = Literal['MATEMATICA', 'COMPUTACION', 'MATEMATICA ITUGS']
Cursor = Annotated[str, Field(max_length=1024)]


class Filters(BaseModel):
    model_config = ConfigDict(extra='forbid')
    anio: Year | None = None
    materia: Subject | None = None
    aprobado: bool | None = None


class EvaluationFilters(Filters):
    limite: int = Field(default=50, ge=1, le=100)
    cursor: Cursor | None = None


class RangeFilters(BaseModel):
    model_config = ConfigDict(extra='forbid')
    desde: Year = 2015
    hasta: Year = 2024

    @model_validator(mode='after')
    def ordered(self):
        if self.desde > self.hasta:
            raise ValueError('desde debe ser menor o igual que hasta')
        return self


class AnnualFilters(BaseModel):
    model_config = ConfigDict(extra='forbid')
    anio: Year


class CareerFilters(AnnualFilters):
    materia: Subject | None = None


class BothFilters(AnnualFilters):
    limite: int = Field(default=50, ge=1, le=100)


class GraphFilters(AnnualFilters):
    materia: Subject | None = None
    aprobado: bool | None = None
    carrera_id: Annotated[str, Field(pattern=r'^carrera:[0-9a-f]{64}$')] | None = None
    limite: int = Field(default=25, ge=1, le=100)


class Meta(BaseModel):
    fuente: Literal['mongodb', 'neo4j']
    filtros: dict[str, JsonValue] = Field(default_factory=dict)
    limite: int | None = None
    siguiente_cursor: str | None = None
    truncado: bool = False
    notas: list[str] = Field(default_factory=list)


T = TypeVar('T')


class Envelope(BaseModel, Generic[T]):
    status: Literal['ok'] = 'ok'
    data: T
    meta: Meta


class ErrorDetail(BaseModel):
    campo: str
    mensaje: str


class ErrorPayload(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail] = Field(default_factory=list)


class APIErrorResponse(BaseModel):
    status: Literal['error'] = 'error'
    error: ErrorPayload


class Statistics(BaseModel):
    registros: int
    aprobados: int
    no_aprobados: int
    porcentaje_aprobacion: float | None
    registros_con_advertencias: int


class Aspirant(BaseModel):
    cohorte_id: str
    sexo: str | None
    anio_nacimiento: int | None


class Career(BaseModel):
    valor: str | None
    estado_normalizacion: str


class Provenance(BaseModel):
    departamento: str | None
    municipio: str | None
    tipo: str | None


class Evaluation(BaseModel):
    id: str
    anio_ingreso: int
    fecha_asignacion: str
    materia: str
    numero_fecha_evaluacion: int
    aprobado: bool
    aspirante: Aspirant
    carrera: Career
    procedencia_educativa: Provenance
    advertencias: list[str]


class ApprovalRow(BaseModel):
    anio: int
    materia: str
    registros: int
    aprobados: int
    porcentaje: float


class CareerRow(BaseModel):
    id: str | None
    carrera: str | None
    estado: str
    registros: int
    aprobados: int


class ProvenanceRow(BaseModel):
    departamento: str | None
    tipo: str | None
    registros: int
    aprobados: int


class BothRow(BaseModel):
    aspirante_cohorte: str
    materias: list[str]


class Catalogs(BaseModel):
    anios: list[int]
    materias: list[str]
    carreras: list[CareerRow]
    tipos_institucion: list[str]


class GraphNode(BaseModel):
    id: str
    tipo: str
    properties: dict[str, JsonValue]


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    tipo: str


class GraphData(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
