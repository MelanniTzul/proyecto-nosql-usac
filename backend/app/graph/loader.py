"""DDL y escrituras solo se ejecutan mediante llamada explícita al cargador."""
from .projector import LABELS, RELATIONS, canonical


def schema_statements():
    return [f'CREATE CONSTRAINT usac_{label.lower()}_id IF NOT EXISTS FOR (n:{label}) REQUIRE n.id IS UNIQUE'
            for label in LABELS] + ['CREATE INDEX usac_evaluacion_anio_resultado IF NOT EXISTS FOR (e:Evaluacion) ON (e.anio_ingreso, e.aprobado)']


def write_graph(tx, graph):
    for label in LABELS:
        rows = [n for n in graph['nodes'] if n['label'] == label]
        if not rows:
            continue
        # Revisar primero: nunca adoptar silenciosamente nodos ajenos o incompatibles.
        records = tx.run(f'UNWIND $rows AS row MATCH (n:{label} {{id: row.id}}) RETURN n.id AS id, labels(n) AS labels, properties(n) AS props', rows=rows)
        by_id = {r['id']: r for r in records}
        for row in rows:
            existing = by_id.get(row['id'])
            if existing and ('USACAdmision' not in existing['labels'] or any(existing['props'].get(k) != v for k, v in row['props'].items())):
                raise ValueError('Nodo existente incompatible; no se modifico')
        tx.run(f'UNWIND $rows AS row MERGE (n:{label} {{id: row.id}}) ON CREATE SET n:USACAdmision, n += row.props', rows=rows).consume()
    grouped = {}
    for edge in graph['edges']:
        if edge['type'] not in RELATIONS or edge['source_label'] not in LABELS or edge['target_label'] not in LABELS:
            raise ValueError('Tipo de relacion no permitido')
        grouped.setdefault((edge['source_label'], edge['type'], edge['target_label']), []).append(edge)
    for (source, kind, target), rows in grouped.items():
        tx.run(f'UNWIND $rows AS row MATCH (a:{source}:USACAdmision {{id: row.source}}), (b:{target}:USACAdmision {{id: row.target}}) MERGE (a)-[:{kind}]->(b)', rows=rows).consume()


def merged_batch(graphs, inventory):
    identities = {(n['label'], n['id']) for g in graphs for n in g['nodes']}
    nodes = [{'label': label, 'id': identity, 'props': inventory.nodes[(label, identity)]}
             for label, identity in sorted(identities)]
    edges = {canonical(e): e for g in graphs for e in g['edges']}
    return {'nodes': nodes, 'edges': list(edges.values())}
