"""Ejecutar un catálogo fijo de 30 consultas de lectura, sin modificar la API."""
import argparse
import hashlib
import json
import time
from pathlib import Path

from pymongo import timeout
from pymongo.errors import PyMongoError

from app.core.config import Settings
from app.database.connections import DatabaseConnections
from app.models.analytics import AnnualFilters, BothFilters, EvaluationFilters, Filters, RangeFilters
from app.services import mongo_analytics

ROOT = Path(__file__).resolve().parents[3]
CATALOG = ROOT / 'consultas/mongodb/catalogo.json'
SOURCE = 'usac_admisiones.evaluaciones'
REUSED = {
    'evaluations': EvaluationFilters,
    'statistics': Filters,
    'approval': RangeFilters,
    'careers': None,
    'provenance': AnnualFilters,
    'both_subjects': BothFilters,
    'catalogs': None,
}
ALLOWED_STAGES = {'$match', '$group', '$sort', '$project', '$limit', '$unwind'}
FORBIDDEN = {'$out', '$merge', '$function', '$accumulator', '$where'}


def load_catalog():
    queries = json.loads(CATALOG.read_text(encoding='utf-8'))
    if [q['id'] for q in queries] != list(range(1, 31)):
        raise ValueError('El catálogo debe contener exactamente ids 1–30')
    for query in queries:
        validate_query(query)
    return queries


def validate_query(query):
    def walk(value):
        if isinstance(value, dict):
            if set(value) & FORBIDDEN:
                raise ValueError('Operador no permitido en consultas de lectura')
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
    walk(query)
    if query['operacion'] == 'existing':
        if query['funcion'] not in REUSED:
            raise ValueError('Función no autorizada')
    elif query['operacion'] == 'aggregate':
        if not query.get('pipeline') or any(len(stage) != 1 or not set(stage) <= ALLOWED_STAGES for stage in query['pipeline']):
            raise ValueError('Pipeline no permitido')
    elif query['operacion'] != 'countDocuments':
        raise ValueError('Operación no autorizada')


def execute_query(connections, query):
    validate_query(query)
    if query['operacion'] == 'existing':
        name = query['funcion']
        args = query['argumentos']
        if name == 'catalogs':
            return mongo_analytics.catalogs(connections)
        if name == 'careers':
            return mongo_analytics.careers(connections)
        result = getattr(mongo_analytics, name)(connections, REUSED[name](**args))
        if name == 'evaluations':
            rows, cursor = result
            return {'registros': rows, 'siguiente_cursor': cursor, 'limite': args['limite']}
        if name == 'both_subjects':
            rows, truncated = result
            return {'registros': rows, 'truncado': truncated, 'limite': args['limite']}
        return result
    collection = connections.mongo['usac_admisiones']['evaluaciones']
    if query['operacion'] == 'countDocuments':
        return {'registros': collection.count_documents(query['filtro'], maxTimeMS=60000)}
    return list(collection.aggregate(query['pipeline'], maxTimeMS=60000,
                                     allowDiskUse=query.get('allowDiskUse', False)))


def catalog_fingerprint(queries):
    return hashlib.sha256(json.dumps(queries, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def verify_results(results, total):
    """Invariantes entre análisis distintos; no reemplaza resultados por constantes."""
    values = {r['id']: r['resultado'] for r in results if r['estado'] == 'ok'}
    checks = []
    def check(name, condition):
        checks.append({'comprobacion': name, 'correcta': bool(condition)})
    if 2 in values:
        check('Conteo total coincide con fuente', values[2]['registros'] == total)
    if 3 in values:
        row = values[3]
        check('Resumen: aprobados + no aprobados = total', row['aprobados'] + row['no_aprobados'] == row['registros'] == total)
    for identity in (4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 18, 21):
        if identity in values:
            check(f'Consulta {identity:02}: partición completa de registros', sum(r['registros'] for r in values[identity]) == total)
    for identity in (5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16):
        if identity in values:
            check(f'Consulta {identity:02}: aprobados dentro del denominador', all(0 <= r['aprobados'] <= r['registros'] for r in values[identity]))
    if 25 in values and 26 in values:
        cohorts = sum(r['aspirantes_cohorte'] for r in values[25])
        check('Consultas 25–26: mismos aspirantes de cohorte', cohorts == sum(r['aspirantes_cohorte'] for r in values[26]))
        check('Consulta 26: histograma reconstruye total', sum(r['registros_por_aspirante'] * r['aspirantes_cohorte'] for r in values[26]) == total)
    if 15 in values and 4 in values:
        check('Consulta 15: total cohorte 2024', sum(r['registros'] for r in values[15]) == next(r['registros'] for r in values[4] if r['anio'] == 2024))
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument('--all', action='store_true', help='Ejecutar las 30 consultas secuencialmente')
    selection.add_argument('--id', type=int, choices=range(1, 31), metavar='1..30')
    selection.add_argument('--list', action='store_true', help='Listar sin conexiones a bases')
    parser.add_argument('--output', type=Path, default=ROOT / 'data/reports/consultas-mongodb.json')
    args = parser.parse_args()
    catalog = load_catalog()
    if args.list:
        for query in catalog:
            print(f"{query['id']:02}. {query['titulo']}")
        return
    selected = catalog if args.all else [q for q in catalog if q['id'] == args.id]
    report = {'fuente': SOURCE, 'modo': 'solo_lectura', 'huella_catalogo': catalog_fingerprint(catalog),
              'estado': 'en_progreso', 'consultas': [], 'comprobaciones': []}
    connections = None
    start = time.perf_counter()
    try:
        connections = DatabaseConnections(Settings())
        collection = connections.mongo['usac_admisiones']['evaluaciones']
        report['documentos_antes'] = collection.count_documents({}, maxTimeMS=60000)
        for query in selected:
            began = time.perf_counter()
            # Presupuesto de consola; no cambia sockets ni límites de la API.
            with timeout(60):
                result = execute_query(connections, query)
            report['consultas'].append({'id': query['id'], 'titulo': query['titulo'], 'estado': 'ok',
                                       'segundos': round(time.perf_counter() - began, 4), 'resultado': result})
            print(f"{query['id']:02}. OK · {query['titulo']}", flush=True)
        report['documentos_despues'] = collection.count_documents({}, maxTimeMS=60000)
        report['comprobaciones'] = verify_results(report['consultas'], report['documentos_antes'])
        if report['documentos_antes'] != report['documentos_despues'] or not all(c['correcta'] for c in report['comprobaciones']):
            raise ValueError('Invariantes de verificación no satisfechas')
        report['estado'] = 'completado'
    except (PyMongoError, ValueError, TypeError, KeyError, OSError) as error:
        report['estado'] = 'incompleto'
        report['error'] = {'tipo': type(error).__name__, 'mensaje': 'La ejecución se detuvo; no se aplican correcciones a los datos.'}
    finally:
        if connections is not None:
            connections.close()
        report['segundos_totales'] = round(time.perf_counter() - start, 4)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f"Reporte: {args.output}")
    if report['estado'] != 'completado':
        parser.exit(1, 'Consultas incompletas; revisar el reporte local (sin secretos).\n')


if __name__ == '__main__':
    main()
