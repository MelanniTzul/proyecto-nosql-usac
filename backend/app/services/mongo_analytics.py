"""Todas las estadísticas se calculan en MongoDB; no crean índices ni datos."""
import base64
import hashlib
import json
import re

from app.graph.projector import key
from app.services.errors import APIError


def match(filters):
    fields = {'anio': 'anio_ingreso', 'materia': 'materia', 'aprobado': 'aprobado'}
    return {target: getattr(filters, field) for field, target in fields.items()
            if getattr(filters, field, None) is not None}


def aggregate(db, pipeline):
    return list(db.mongo['usac_admisiones']['evaluaciones'].aggregate(
        pipeline, maxTimeMS=int(db.settings.api_query_timeout_seconds * 1000), allowDiskUse=False))


def statistics(db, filters):
    rows = aggregate(db, [{'$match': match(filters)}, {'$group': {
        '_id': None, 'registros': {'$sum': 1},
        'aprobados': {'$sum': {'$cond': ['$aprobado', 1, 0]}},
        'registros_con_advertencias': {'$sum': {'$cond': [{'$gt': [{'$size': '$calidad.advertencias'}, 0]}, 1, 0]}}
    }}])
    row = rows[0] if rows else {'registros': 0, 'aprobados': 0, 'registros_con_advertencias': 0}
    row.pop('_id', None)
    row['no_aprobados'] = row['registros'] - row['aprobados']
    row['porcentaje_aprobacion'] = round(100 * row['aprobados'] / row['registros'], 2) if row['registros'] else None
    return row


def fingerprint(filters):
    return hashlib.sha256(json.dumps(match(filters), sort_keys=True).encode()).hexdigest()


def encode_cursor(identity, filters):
    return base64.urlsafe_b64encode(json.dumps({'id': identity, 'f': fingerprint(filters)}).encode()).decode()


def decode_cursor(value, filters):
    try:
        data = json.loads(base64.b64decode(value, altchars=b'-_', validate=True))
        if set(data) != {'id', 'f'} or data['f'] != fingerprint(filters) or not re.fullmatch(r'[0-9a-f]{64}', data['id']):
            raise ValueError
        return data['id']
    except (ValueError, TypeError, KeyError, UnicodeError):
        raise APIError(422, 'INVALID_CURSOR', 'El cursor no es válido para estos filtros.') from None


def evaluations(db, filters):
    query = match(filters)
    if filters.cursor:
        query['_id'] = {'$gt': decode_cursor(filters.cursor, filters)}
    projection = {k: 1 for k in ('anio_ingreso', 'fecha_asignacion', 'materia',
        'numero_fecha_evaluacion', 'aprobado', 'aspirante.cohorte_id', 'aspirante.sexo',
        'aspirante.anio_nacimiento', 'carrera', 'procedencia_educativa', 'calidad.advertencias')}
    cursor = db.mongo['usac_admisiones']['evaluaciones'].find(query, projection).sort('_id', 1).limit(filters.limite + 1).max_time_ms(int(db.settings.api_query_timeout_seconds * 1000))
    rows = list(cursor)
    more = len(rows) > filters.limite
    rows = rows[:filters.limite]
    next_cursor = encode_cursor(rows[-1]['_id'], filters) if more else None
    for row in rows:
        row['id'] = row.pop('_id')
        row['advertencias'] = row.pop('calidad')['advertencias']
    return rows, next_cursor


def approval(db, filters):
    rows = aggregate(db, [{'$match': {'anio_ingreso': {'$gte': filters.desde, '$lte': filters.hasta}}},
        {'$group': {'_id': {'anio': '$anio_ingreso', 'materia': '$materia'}, 'registros': {'$sum': 1},
                    'aprobados': {'$sum': {'$cond': ['$aprobado', 1, 0]}}}},
        {'$sort': {'_id.anio': 1, '_id.materia': 1}}])
    return [dict(**row['_id'], registros=row['registros'], aprobados=row['aprobados'],
                 porcentaje=round(100 * row['aprobados'] / row['registros'], 2)) for row in rows]


def careers(db, filters=None):
    rows = aggregate(db, [{'$match': match(filters) if filters else {}},
        {'$group': {'_id': {'valor': '$carrera.valor', 'estado': '$carrera.estado_normalizacion'},
                    'registros': {'$sum': 1}, 'aprobados': {'$sum': {'$cond': ['$aprobado', 1, 0]}}}},
        {'$sort': {'registros': -1, '_id.valor': 1, '_id.estado': 1}}])
    return [dict(id=key('carrera', row['_id']['valor'], row['_id']['estado']) if row['_id']['valor'] else None,
                 carrera=row['_id']['valor'], estado=row['_id']['estado'],
                 registros=row['registros'], aprobados=row['aprobados']) for row in rows]


def provenance(db, filters):
    rows = aggregate(db, [{'$match': {'anio_ingreso': filters.anio}},
        {'$group': {'_id': {'departamento': '$procedencia_educativa.departamento',
                           'tipo': '$procedencia_educativa.tipo'}, 'registros': {'$sum': 1},
                    'aprobados': {'$sum': {'$cond': ['$aprobado', 1, 0]}}}},
        {'$sort': {'registros': -1, '_id.departamento': 1, '_id.tipo': 1}}])
    return [dict(**row['_id'], registros=row['registros'], aprobados=row['aprobados']) for row in rows]


def both_subjects(db, filters):
    rows = aggregate(db, [{'$match': {'anio_ingreso': filters.anio, 'aprobado': True,
                                     'materia': {'$in': ['MATEMATICA', 'COMPUTACION']}}},
        {'$group': {'_id': '$aspirante.cohorte_id', 'materias': {'$addToSet': '$materia'}}},
        {'$match': {'materias': {'$all': ['MATEMATICA', 'COMPUTACION']}}},
        {'$sort': {'_id': 1}}, {'$limit': filters.limite + 1}])
    return [dict(aspirante_cohorte=row['_id'], materias=sorted(row['materias'])) for row in rows[:filters.limite]], len(rows) > filters.limite


def catalogs(db):
    rows = aggregate(db, [{'$facet': {
        'anios': [{'$group': {'_id': '$anio_ingreso'}}, {'$sort': {'_id': 1}}],
        'materias': [{'$group': {'_id': '$materia'}}, {'$sort': {'_id': 1}}],
        'tipos': [{'$group': {'_id': '$procedencia_educativa.tipo'}}, {'$sort': {'_id': 1}}]
    }}])[0]
    return {'anios': [r['_id'] for r in rows['anios']],
            'materias': [r['_id'] for r in rows['materias']],
            'tipos_institucion': [r['_id'] for r in rows['tipos'] if r['_id'] is not None],
            'carreras': careers(db)}
