import hashlib
import json
from datetime import date

VERSION = '1'
LABELS = ('Evaluacion', 'AspiranteCohorte', 'Cohorte', 'Materia', 'CarreraObservada',
          'LocalidadEducativa', 'Departamento', 'TipoInstitucion')
RELATIONS = {'TIENE_REGISTRO', 'EN_COHORTE', 'DE_MATERIA', 'ASPIRA_A',
             'PROCEDENCIA_EDUCATIVA', 'EN_DEPARTAMENTO', 'TIPO_INSTITUCION'}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def key(kind, *values):
    return kind + ':' + hashlib.sha256(canonical(values).encode()).hexdigest()


def project(document):
    """No interpreta el correlativo como identidad entre años. Falla ante esquema inválido."""
    d = document
    year, a = d['anio_ingreso'], d['aspirante']
    if type(year) is not int or not 2015 <= year <= 2024:
        raise ValueError('Cohorte invalida')
    if a['cohorte_id'] != f"{year}:{a['correlativo_original']}":
        raise ValueError('Identidad de cohorte incompatible')
    if type(d['aprobado']) is not bool or type(d['numero_fecha_evaluacion']) is not int:
        raise ValueError('Resultado o convocatoria invalido')
    if d['numero_fecha_evaluacion'] not in range(1, 6):
        raise ValueError('Convocatoria invalida')
    date.fromisoformat(d['fecha_asignacion'])
    if not isinstance(d['_id'], str) or len(d['_id']) != 64:
        raise ValueError('Identificador documental invalido')
    warnings = d['calidad']['advertencias']
    if not isinstance(warnings, list) or any(not isinstance(v, str) for v in warnings):
        raise ValueError('Advertencias invalidas')
    nodes, edges = [], []

    def node(label, identity, **properties):
        props = {k: v for k, v in properties.items() if v is not None}
        item = {'label': label, 'id': identity, 'props': props}
        nodes.append(item)
        return (label, identity)

    def edge(source, kind, target):
        edges.append({'source_label': source[0], 'source': source[1], 'type': kind,
                      'target_label': target[0], 'target': target[1]})

    source = d['fuente']
    e = node('Evaluacion', d['_id'], anio_ingreso=year,
             fecha_asignacion=d['fecha_asignacion'], convocatoria=d['numero_fecha_evaluacion'],
             aprobado=d['aprobado'], advertencias=warnings, archivo=source['archivo'],
             sha256_archivo=source['sha256_archivo'], numero_registro=source['numero_registro'],
             version_transformacion=d['version_transformacion'])
    aspirant = node('AspiranteCohorte', a['cohorte_id'], anio_ingreso=year,
                    correlativo=a['correlativo_original'], sexo=a['sexo'],
                    anio_nacimiento=a['anio_nacimiento'])
    edge(aspirant, 'TIENE_REGISTRO', e)
    edge(e, 'EN_COHORTE', node('Cohorte', str(year), anio=year))
    edge(e, 'DE_MATERIA', node('Materia', key('materia', d['materia']), nombre=d['materia']))
    career = d['carrera']
    if career['valor'] is not None:
        edge(e, 'ASPIRA_A', node('CarreraObservada', key('carrera', career['valor'], career['estado_normalizacion']),
                                 nombre=career['valor'], estado_normalizacion=career['estado_normalizacion']))
    p = d['procedencia_educativa']
    department = node('Departamento', key('departamento', p['departamento']), nombre=p['departamento']) if p['departamento'] else None
    if p['municipio']:
        precision = 'no_garantizada' if year >= 2022 else 'etiqueta_publicada'
        location = node('LocalidadEducativa', key('localidad', p['departamento'], p['municipio'], precision),
                        nombre_observado=p['municipio'], precision_fuente=precision)
        edge(e, 'PROCEDENCIA_EDUCATIVA', location)
        if department:
            edge(location, 'EN_DEPARTAMENTO', department)
    if p['tipo']:
        edge(e, 'TIPO_INSTITUCION', node('TipoInstitucion', key('tipo', p['tipo']), nombre=p['tipo']))
    return {'nodes': nodes, 'edges': edges}


class Inventory:
    def __init__(self):
        self.nodes = {}
        self.edges = set()
        self.digest = hashlib.sha256()
        self.documents = 0

    def add(self, document):
        graph = project(document)
        for n in graph['nodes']:
            identity = (n['label'], n['id'])
            # Atributos ausentes no contradicen un atributo conocido.
            previous = self.nodes.setdefault(identity, {})
            for field, value in n['props'].items():
                if field in previous and previous[field] != value:
                    raise ValueError(f'Conflicto en {n["label"]}.{field}')
                previous[field] = value
        self.edges.update(tuple(e[k] for k in ('source_label', 'source', 'type', 'target_label', 'target')) for e in graph['edges'])
        self.digest.update((canonical(graph) + '\n').encode())
        self.documents += 1
        return graph

    def report(self):
        return {'version': VERSION, 'documentos': self.documents, 'huella': self.digest.hexdigest(),
                'nodos': {label: sum(k[0] == label for k in self.nodes) for label in LABELS},
                'relaciones': {kind: sum(e[2] == kind for e in self.edges) for kind in sorted(RELATIONS)}}
