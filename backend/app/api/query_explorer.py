from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.api.analytics import databases
from app.models.analytics import APIErrorResponse, Envelope, Meta
from app.models.query_explorer import NeoQueryParameters, NoQueryParameters, QueryCatalogResponse, QueryExecution
from app.services import query_explorer

router = APIRouter(prefix='/consultas', tags=['Consultas NoSQL'], responses={
    422: {'model': APIErrorResponse}, 404: {'model': APIErrorResponse},
    503: {'model': APIErrorResponse}, 504: {'model': APIErrorResponse},
    500: {'model': APIErrorResponse},
})
DB = Annotated[object, Depends(databases)]


@router.get('', response_model=QueryCatalogResponse)
def catalog():
    """Lista cerrada de 30 consultas MongoDB y 6 Cypher; no ejecuta consultas."""
    return {'status': 'ok', 'data': query_explorer.descriptions(),
            'meta': {'fuente': 'catalogo', 'solo_lectura': True}}


@router.get('/mongodb/{consulta_id}', response_model=Envelope[QueryExecution])
def mongodb(db: DB, consulta_id: Annotated[int, Path(ge=1, le=30)],
            parameters: Annotated[NoQueryParameters, Query()]):
    """Ejecuta el id del catálogo con sus argumentos predefinidos. No acepta código."""
    result, truncated = query_explorer.mongo_query(db, consulta_id)
    return {'status': 'ok', 'data': result, 'meta': Meta(
        fuente='mongodb', limite=500, truncado=truncated,
        notas=['Solo lectura. Parámetros fijos del catálogo; no se ejecuta código del navegador.',
               'Los límites originales de las consultas 01 y 27 se conservan.'])}


@router.get('/neo4j/{consulta_id}', response_model=Envelope[QueryExecution])
def neo4j(db: DB, consulta_id: Annotated[int, Path(ge=1, le=6)],
          parameters: Annotated[NeoQueryParameters, Query()]):
    """Ejecuta uno de los seis archivos Cypher existentes con parámetros validados."""
    result, truncated, values = query_explorer.neo_query(db, consulta_id, parameters)
    return {'status': 'ok', 'data': result, 'meta': Meta(
        fuente='neo4j', filtros=values, limite=500, truncado=truncated,
        notas=['Se conserva LIMIT 100 en consultas 03 y 05.',
               'El grafo está acotado a 500 nodos y 800 relaciones.'])}
