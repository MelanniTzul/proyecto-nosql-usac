from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Request

from app.models.analytics import (
    AnnualFilters, APIErrorResponse, ApprovalRow, BothFilters, BothRow, Catalogs,
    CareerFilters, CareerRow, Envelope, Evaluation, EvaluationFilters, Filters,
    GraphData, GraphFilters, Meta, ProvenanceRow, RangeFilters, Statistics,
)
from app.services import graph_queries, mongo_analytics

router = APIRouter(responses={422: {'model': APIErrorResponse}, 503: {'model': APIErrorResponse},
                             504: {'model': APIErrorResponse}, 500: {'model': APIErrorResponse}})


def databases(request: Request):
    return request.app.state.databases


DB = Annotated[object, Depends(databases)]
NOTES = ['Los conteos representan registros de fuente, incluidas repeticiones originales.',
         'Aspirante de cohorte significa año y correlativo; no persona global.']


def envelope(data, source, filters=None, **kwargs):
    values = filters.model_dump(exclude_none=True, exclude={'cursor', 'limite'}) if filters else {}
    return {'status': 'ok', 'data': data, 'meta': Meta(fuente=source, filtros=values, notas=NOTES, **kwargs)}


@router.get('/estadisticas', response_model=Envelope[Statistics], tags=['Estadísticas'])
def statistics(db: DB, filters: Annotated[Filters, Query()]):
    """Totales MongoDB; porcentaje nulo cuando no hay registros."""
    return envelope(mongo_analytics.statistics(db, filters), 'mongodb', filters)


@router.get('/evaluaciones', response_model=Envelope[list[Evaluation]], tags=['Evaluaciones'])
def evaluations(db: DB, filters: Annotated[EvaluationFilters, Query()]):
    """Página ordenada por id; continuar con siguiente_cursor y los mismos filtros."""
    data, cursor = mongo_analytics.evaluations(db, filters)
    return envelope(data, 'mongodb', filters, limite=filters.limite, siguiente_cursor=cursor)


@router.get('/catalogos', response_model=Envelope[Catalogs], tags=['Catálogos'])
def catalogs(db: DB):
    """Categorías reales, con carreras recortadas y ausentes diferenciadas."""
    return envelope(mongo_analytics.catalogs(db), 'mongodb')


@router.get('/estadisticas/aprobacion', response_model=Envelope[list[ApprovalRow]], tags=['Estadísticas'])
def approval(db: DB, filters: Annotated[RangeFilters, Query()]):
    """Aprobación por año y materia, calculada en MongoDB."""
    return envelope(mongo_analytics.approval(db, filters), 'mongodb', filters)


@router.get('/resultados/carreras', response_model=Envelope[list[CareerRow]], tags=['Estadísticas'])
def careers(db: DB, filters: Annotated[CareerFilters, Query()]):
    """Carreras por valor y estado; incluye la categoría ausente (id nulo)."""
    return envelope(mongo_analytics.careers(db, filters), 'mongodb', filters)


@router.get('/procedencia', response_model=Envelope[list[ProvenanceRow]], tags=['Estadísticas'])
def provenance(db: DB, filters: Annotated[AnnualFilters, Query()]):
    """Procedencia educativa, no residencia. Incluye datos ausentes como nulos."""
    return envelope(mongo_analytics.provenance(db, filters), 'mongodb', filters)


@router.get('/resultados/ambas-materias', response_model=Envelope[list[BothRow]], tags=['Estadísticas'])
def both_subjects(db: DB, filters: Annotated[BothFilters, Query()]):
    """Aprobación informada en ambas materias; no acredita admisión definitiva."""
    data, truncated = mongo_analytics.both_subjects(db, filters)
    return envelope(data, 'mongodb', filters, limite=filters.limite, truncado=truncated)


@router.get('/grafo', response_model=Envelope[GraphData], tags=['Grafos'])
def graph(db: DB, filters: Annotated[GraphFilters, Query()]):
    """Subgrafo Neo4j: hasta 100 evaluaciones, 500 nodos y 800 relaciones."""
    data, truncated = graph_queries.graph(db, filters=filters)
    return envelope(data, 'neo4j', filters, limite=filters.limite, truncado=truncated)


@router.get('/grafo/aspirantes/{cohorte_id}', response_model=Envelope[GraphData], tags=['Grafos'],
            responses={404: {'model': APIErrorResponse}})
def aspirant_graph(db: DB,
                   cohorte_id: Annotated[str, Path(pattern=r'^(201[5-9]|202[0-4]):[0-9a-f]{20,32}$', max_length=37)],
                   limite: Annotated[int, Query(ge=1, le=100)] = 25):
    """Registros del correlativo solo dentro de su cohorte."""
    data, truncated = graph_queries.graph(db, cohort_id=cohorte_id, limit=limite)
    result = envelope(data, 'neo4j', limite=limite, truncado=truncated)
    result['meta'].filtros = {'cohorte_id': cohorte_id}
    return result
