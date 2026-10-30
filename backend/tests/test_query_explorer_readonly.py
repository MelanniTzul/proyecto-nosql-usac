"""Las 36 consultas pasan por HTTP con bases reales y solo lecturas."""
import json
import os
import unittest
from pathlib import Path
from fastapi.testclient import TestClient
from neo4j import READ_ACCESS
from app.main import create_app
from app.graph.projector import key


@unittest.skipUnless(os.environ.get('USAC_RUN_DB_TESTS') == '1', 'Requiere bases reales')
class QueryExplorerReadOnlyTests(unittest.TestCase):
    def test_all_30_mongo_and_6_neo4j_over_http(self):
        records = []
        with TestClient(create_app()) as client:
            db = client.app.state.databases
            collection = db.mongo['usac_admisiones']['evaluaciones']
            def counts():
                with db.neo4j.session(database='neo4j', default_access_mode=READ_ACCESS) as session:
                    graph = session.execute_read(lambda tx: (
                        tx.run('MATCH (n) RETURN count(n) AS c').single()['c'],
                        tx.run('MATCH ()-[r]->() RETURN count(r) AS c').single()['c']))
                return {'mongo': collection.count_documents({}), 'nodos': graph[0], 'relaciones': graph[1]}
            before = counts()
            for identity in range(1, 31):
                with self.subTest(mongodb=identity):
                    response = client.get(f'/api/consultas/mongodb/{identity}')
                    self.assertEqual(response.status_code, 200, response.text[:400])
                    body = response.json()
                    self.assertEqual(body['data']['id'], identity)
                    self.assertEqual(body['meta']['fuente'], 'mongodb')
                    records.append({'motor': 'mongodb', 'id': identity, 'status': response.status_code,
                                    'filas': body['data']['filas'], 'segundos': body['data']['segundos']})
            sample = collection.find_one({'anio_ingreso': 2024, 'materia': 'MATEMATICA', 'aprobado': False, 'carrera.estado_normalizacion': 'completa'})
            params = {1: {'desde': 2024, 'hasta': 2024},
                      2: {'anio': 2024, 'materia': 'MATEMATICA'},
                      3: {'anio': 2024, 'materia': 'MATEMATICA', 'aprobado': False,
                          'carrera_id': key('carrera', sample['carrera']['valor'], sample['carrera']['estado_normalizacion'])},
                      4: {'cohorte_id': sample['aspirante']['cohorte_id']},
                      5: {'anio': 2024}, 6: {'anio': 2024}}
            for identity in range(1, 7):
                with self.subTest(neo4j=identity):
                    response = client.get(f'/api/consultas/neo4j/{identity}', params=params[identity])
                    self.assertEqual(response.status_code, 200, response.text[:400])
                    body = response.json()
                    self.assertEqual(body['meta']['fuente'], 'neo4j')
                    self.assertTrue(body['data']['resultado'])
                    if identity in (3, 4):
                        graph = body['data']['grafo']
                        self.assertTrue(graph['nodes'])
                        ids = {n['id'] for n in graph['nodes']}
                        self.assertTrue(all(e['source'] in ids and e['target'] in ids for e in graph['edges']))
                    records.append({'motor': 'neo4j', 'id': identity, 'status': response.status_code,
                                    'filas': body['data']['filas'], 'segundos': body['data']['segundos']})
            after = counts()
            self.assertEqual(before, after)
        output = Path(__file__).resolve().parents[2] / 'data/reports/explorador-consultas'
        output.mkdir(parents=True, exist_ok=True)
        (output / 'api.json').write_text(json.dumps({'antes': before, 'despues': after, 'consultas': records}, indent=2) + '\n')
