"""Catálogo cerrado: ids y parámetros de negocio, nunca texto ejecutable del cliente."""
import re
import time
from itertools import islice
from pathlib import Path

from neo4j import READ_ACCESS, unit_of_work
from pymongo import timeout

from app.queries.mongodb import execute_query, load_catalog
from app.services.errors import APIError
from app.services.graph_queries import serialize

ROOT = Path(__file__).resolve().parents[3]
MAX_ROWS = 500
NEO_QUERIES = (
    (1, '01_aprobacion.cypher', 'Aprobación por año y materia', ['desde', 'hasta'], {'desde': 2015, 'hasta': 2024}, 'tabla'),
    (2, '02_carreras.cypher', 'Resultados por carrera y materia', ['anio', 'materia'], {'anio': 2024, 'materia': 'MATEMATICA'}, 'tabla'),
    (3, '03_visualizacion.cypher', 'Aspirantes, evaluaciones y carreras', ['anio', 'materia', 'carrera_id', 'aprobado'], {'anio': 2024, 'materia': 'MATEMATICA', 'aprobado': False}, 'grafo'),
    (4, '04_aspirante.cypher', 'Registros del aspirante de cohorte', ['cohorte_id'], {}, 'grafo'),
    (5, '05_ambas_materias.cypher', 'Aprobación en ambas materias', ['anio'], {'anio': 2024}, 'tabla'),
    (6, '06_procedencia.cypher', 'Procedencia educativa', ['anio'], {'anio': 2024}, 'tabla'),
)


def descriptions():
    mongo = [{'id': q['id'], 'titulo': q['titulo'], 'objetivo': q['objetivo'],
              'explicacion': q['explicacion'], 'parametros': [],
              'valores_defecto': q.get('argumentos', {}), 'visualizacion': 'tabla'} for q in load_catalog()]
    neo = [{'id': identity, 'titulo': title, 'objetivo': title,
            'explicacion': f'Consulta de lectura existente: {filename}. Parámetros separados del texto Cypher.',
            'parametros': fields, 'valores_defecto': defaults, 'visualizacion': view}
           for identity, filename, title, fields, defaults, view in NEO_QUERIES]
    return {'mongodb': mongo, 'neo4j': neo}


def cap_lists(value):
    """Acota la serialización sin cambiar pipelines ni denominadores del análisis."""
    capped = False
    if isinstance(value, list):
        capped = len(value) > MAX_ROWS
        output = []
        for item in value[:MAX_ROWS]:
            converted, flag = cap_lists(item)
            output.append(converted)
            capped |= flag
        return output, capped
    if isinstance(value, dict):
        output = {}
        for name, item in value.items():
            output[name], flag = cap_lists(item)
            capped |= flag
        return output, capped
    return value, False


def mongo_query(connections, identity):
    query = next((q for q in load_catalog() if q['id'] == identity), None)
    if query is None:
        raise APIError(404, 'QUERY_NOT_FOUND', 'Consulta no disponible en el catálogo.')
    start = time.perf_counter()
    # Contexto local al hilo; las rutas actuales conservan sus presupuestos.
    with timeout(60):
        result = execute_query(connections, query)
    result, capped = cap_lists(result)
    original_limit = isinstance(result, dict) and (result.get('truncado', False) or bool(result.get('siguiente_cursor')))
    if isinstance(result, list):
        count = len(result)
    elif isinstance(result, dict) and isinstance(result.get('registros'), list):
        count = len(result['registros'])
    else:
        count = 1
    return {'id': identity, 'titulo': query['titulo'], 'resultado': result,
            'filas': count, 'segundos': round(time.perf_counter() - start, 4)}, bool(capped or original_limit)


def neo_definition(identity):
    item = next((q for q in NEO_QUERIES if q[0] == identity), None)
    if item is None:
        raise APIError(404, 'QUERY_NOT_FOUND', 'Consulta no disponible en el catálogo.')
    path = ROOT / 'consultas/neo4j' / item[1]
    text = path.read_text(encoding='utf-8')
    # Defensa sobre archivos del proyecto; el navegador no puede elegir rutas ni texto.
    if not text.lstrip().startswith('MATCH') or re.search(r'\b(CREATE|MERGE|DELETE|DETACH|SET|REMOVE|DROP|CALL|LOAD)\b', text, re.I):
        raise APIError(500, 'UNSAFE_QUERY', 'La consulta del catálogo no cumple el contrato de lectura.')
    return item, text


def parameters_for(definition, supplied):
    allowed = definition[3]
    values = supplied.model_dump(exclude_none=True)
    if set(values) - set(allowed):
        raise APIError(422, 'INVALID_PARAMETERS', 'Hay parámetros que esta consulta no admite.')
    if set(allowed) - set(values):
        raise APIError(422, 'MISSING_PARAMETERS', 'Completa los parámetros requeridos de la consulta.')
    if 'desde' in values and values['desde'] > values['hasta']:
        raise APIError(422, 'INVALID_RANGE', 'Desde no puede superar hasta.')
    return values


def path_row(record):
    nodes = {}
    paths = []
    for path in record.values():
        paths.append(path)
        for node in path.nodes:
            for label in ('AspiranteCohorte', 'Evaluacion', 'Materia', 'CarreraObservada'):
                if label in node.labels:
                    nodes[label] = node
    result = {}
    mapping = {'AspiranteCohorte': {'aspirante_cohorte': 'id'},
               'Evaluacion': {'evaluacion': 'id', 'anio_ingreso': 'anio_ingreso', 'aprobado': 'aprobado'},
               'Materia': {'materia': 'nombre'},
               'CarreraObservada': {'carrera': 'nombre', 'estado_carrera': 'estado_normalizacion'}}
    for label, fields in mapping.items():
        if label in nodes:
            for target, source in fields.items():
                result[target] = nodes[label].get(source)
    return result, paths


def neo_query(connections, identity, supplied):
    definition, text = neo_definition(identity)
    params = parameters_for(definition, supplied)
    start = time.perf_counter()

    @unit_of_work(timeout=30)
    def read(tx):
        cursor = tx.run(text, params)
        records = list(islice(cursor, MAX_ROWS + 1))
        paths, rows = [], []
        for record in records[:MAX_ROWS]:
            if definition[5] == 'grafo':
                row, row_paths = path_row(record)
                rows.append(row)
                paths.extend(row_paths)
            else:
                rows.append(dict(record))
        graph = None
        graph_cap = False
        if definition[5] == 'grafo':
            graph, graph_cap = serialize(paths)
        # Los archivos 03 y 05 ya tienen LIMIT 100, que se conserva.
        limited = len(records) > MAX_ROWS or graph_cap or (identity in (3, 5) and len(records) == 100)
        return rows, graph, limited

    with connections.neo4j.session(database='neo4j', default_access_mode=READ_ACCESS) as session:
        rows, graph, limited = session.execute_read(read)
    return {'id': identity, 'titulo': definition[2], 'resultado': rows, 'grafo': graph,
            'filas': len(rows), 'segundos': round(time.perf_counter() - start, 4)}, limited, params
