import argparse
import hashlib
import json
from pathlib import Path

from pymongo import MongoClient
from app.core.config import Settings
from .projector import Inventory, VERSION, LABELS, project, canonical
from .loader import merged_batch, schema_statements, write_graph


def main():
    parser = argparse.ArgumentParser(description='Proyeccion MongoDB → Neo4j; simulacion predeterminada')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--dry-run', action='store_true')
    mode.add_argument('--execute', action='store_true')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--batch-size', type=int, default=500)
    parser.add_argument('--output-dir', type=Path, default=Path('data/reports/neo4j'))
    args = parser.parse_args()
    if not 1 <= args.batch_size <= 2000:
        parser.error('batch-size debe estar entre 1 y 2000')
    if args.resume and not args.execute:
        parser.error('--resume requiere --execute')
    settings = Settings()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    try:
        with MongoClient(host=settings.mongo_host, port=settings.mongo_port,
                         username=settings.mongo_root_username.get_secret_value(),
                         password=settings.mongo_root_password.get_secret_value(),
                         authSource=settings.mongo_auth_source, timeoutMS=30000) as client:
            collection = client['usac_admisiones']['evaluaciones']
            inventory = Inventory()
            for document in collection.find({}).sort('_id', 1).batch_size(args.batch_size):
                inventory.add(document)
            report = inventory.report()
            if not report['documentos']:
                raise ValueError('Fuente vacia')
            report.update(modo='execute' if args.execute else 'dry-run', escrituras_neo4j=False,
                          fuente='usac_admisiones.evaluaciones', base_neo4j=settings.neo4j_database)
            if args.execute:
                execute(collection, settings, args, inventory, report)
            (args.output_dir / 'simulacion.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
            print(json.dumps(report, indent=2, ensure_ascii=False))
    except Exception as error:
        # No revelar excepciones de controladores ni documentos.
        parser.exit(1, f'Proyeccion incompleta ({type(error).__name__}); revisar fuente y checkpoint.\n')


def execute(collection, settings, args, inventory, report):
    from neo4j import GraphDatabase
    if settings.neo4j_database != 'neo4j':
        raise ValueError('Destino no autorizado: se requiere neo4j')
    checkpoint = args.output_dir / 'checkpoint.json'
    identity = {'huella': report['huella'], 'version': VERSION,
                'base': settings.neo4j_database, 'host': settings.neo4j_host,
                'puerto': settings.neo4j_port}
    last = None
    if args.resume:
        saved = json.loads(checkpoint.read_text())
        if saved['fuente'] != identity:
            raise ValueError('Checkpoint incompatible')
        last = saved['ultimo_id']
    with GraphDatabase.driver(f'bolt://{settings.neo4j_host}:{settings.neo4j_port}',
                              auth=(settings.neo4j_username.get_secret_value(), settings.neo4j_password.get_secret_value()),
                              max_transaction_retry_time=0) as driver:
        with driver.session(database=settings.neo4j_database) as session:
            # Inspeccionar el destino completo antes de DDL o inserciones.
            def inspect(tx):
                for label in LABELS:
                    for row in tx.run(f'MATCH (n:{label}) RETURN n.id AS id, labels(n) AS labels, properties(n) AS props'):
                        expected = inventory.nodes.get((label, row['id']))
                        if expected is not None and ('USACAdmision' not in row['labels'] or any(row['props'].get(k) != v for k,v in expected.items())):
                            raise ValueError('Colision en destino')
                tx.run('SHOW CONSTRAINTS').consume()
                tx.run('SHOW INDEXES').consume()
            session.execute_read(inspect)
            for statement in schema_statements():
                session.run(statement).consume()
            report['escrituras_neo4j'] = True
            query = {'_id': {'$gt': last}} if last else {}
            graphs, current = [], None
            verification = hashlib.sha256()
            # Volver a comprobar toda la fuente antes de procesar los lotes.
            for document in collection.find({}).sort('_id', 1):
                verification.update((canonical(project(document)) + '\n').encode())
            if verification.hexdigest() != report['huella']:
                raise ValueError('La fuente cambio')
            def commit():
                session.execute_write(write_graph, merged_batch(graphs, inventory))
                temporary = checkpoint.with_suffix('.tmp')
                temporary.write_text(json.dumps({'fuente': identity, 'ultimo_id': current}) + '\n')
                temporary.replace(checkpoint)
            for document in collection.find(query).sort('_id', 1).batch_size(args.batch_size):
                graph = project(document)
                # La proyección debe coincidir con la instantánea prevalidada.
                for node in graph['nodes']:
                    known = inventory.nodes.get((node['label'], node['id']))
                    if known is None or any(known.get(k) != v for k,v in node['props'].items()):
                        raise ValueError('Fuente modificada durante carga')
                graphs.append(graph)
                current = document['_id']
                if len(graphs) == args.batch_size:
                    commit()
                    graphs = []
            if graphs:
                commit()
            report['estado'] = 'completado'


if __name__ == '__main__':
    main()
