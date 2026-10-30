"""Cypher parametrizado, solo lectura y expansión limitada a evaluaciones elegidas."""
from neo4j import READ_ACCESS, unit_of_work

from app.graph.projector import LABELS, key
from app.services.errors import APIError

SELECT_EVALUATIONS = '''
MATCH (e:Evaluacion:USACAdmision)
WHERE e.anio_ingreso = $anio
 AND ($aprobado IS NULL OR e.aprobado = $aprobado)
 AND ($materia IS NULL OR EXISTS {
   MATCH (e)-[:DE_MATERIA]->(m:Materia:USACAdmision) WHERE m.nombre = $materia })
 AND ($carrera_id IS NULL OR EXISTS {
   MATCH (e)-[:ASPIRA_A]->(r:CarreraObservada:USACAdmision) WHERE r.id = $carrera_id })
RETURN e.id AS id ORDER BY e.id LIMIT $fetch
'''
SELECT_ASPIRANT = '''
MATCH (a:AspiranteCohorte:USACAdmision {id:$cohorte_id})-[:TIENE_REGISTRO]->(e:Evaluacion:USACAdmision)
RETURN e.id AS id ORDER BY e.id LIMIT $fetch
'''
EXPAND = '''
MATCH p=(e:Evaluacion:USACAdmision)-[:DE_MATERIA|EN_COHORTE|ASPIRA_A|PROCEDENCIA_EDUCATIVA|TIPO_INSTITUCION]->(:USACAdmision)
WHERE e.id IN $ids RETURN p
UNION ALL
MATCH p=(:AspiranteCohorte:USACAdmision)-[:TIENE_REGISTRO]->(e:Evaluacion:USACAdmision)
WHERE e.id IN $ids RETURN p
UNION ALL
MATCH p=(e:Evaluacion:USACAdmision)-[:PROCEDENCIA_EDUCATIVA]->(:LocalidadEducativa:USACAdmision)-[:EN_DEPARTAMENTO]->(:Departamento:USACAdmision)
WHERE e.id IN $ids RETURN p
'''


def serialize(paths, max_nodes=500, max_edges=800):
    nodes, edges = {}, {}
    truncated = False

    def node_data(node):
        label = next((label for label in LABELS if label in node.labels), None)
        if label is None:
            raise ValueError('Etiqueta inesperada en grafo')
        return {'id': f'{label}:{node["id"]}', 'tipo': label, 'properties': dict(node)}

    for path in paths:
        for relationship in path.relationships:
            source, target = node_data(relationship.start_node), node_data(relationship.end_node)
            identity = key('relacion', source['id'], relationship.type, target['id'])
            if identity in edges:
                continue
            extra = len({source['id'], target['id']} - nodes.keys())
            if len(nodes) + extra > max_nodes or len(edges) >= max_edges:
                truncated = True
                continue
            nodes[source['id']] = source
            nodes[target['id']] = target
            edges[identity] = {'id': identity, 'source': source['id'], 'target': target['id'], 'tipo': relationship.type}
    return {'nodes': sorted(nodes.values(), key=lambda n: n['id']),
            'edges': sorted(edges.values(), key=lambda e: e['id'])}, truncated


def graph(db, filters=None, cohort_id=None, limit=None):
    maximum = filters.limite if filters is not None else limit
    params = filters.model_dump(exclude={'limite'}) if filters is not None else {'cohorte_id': cohort_id}
    params['fetch'] = maximum + 1
    selection = SELECT_EVALUATIONS if filters is not None else SELECT_ASPIRANT
    timeout = db.settings.api_query_timeout_seconds

    @unit_of_work(timeout=timeout)
    def read(tx):
        ids = [row['id'] for row in tx.run(selection, params)]
        if not ids and cohort_id is not None:
            raise APIError(404, 'NOT_FOUND', 'No se encontraron registros del aspirante de cohorte.')
        if not ids:
            return {'nodes': [], 'edges': []}, False
        paths = [row['p'] for row in tx.run(EXPAND, ids=ids[:maximum])]
        data, capped = serialize(paths)
        return data, capped or len(ids) > maximum

    with db.neo4j.session(database='neo4j', default_access_mode=READ_ACCESS) as session:
        return session.execute_read(read)
