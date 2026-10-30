import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from app.main import create_app
from app.models.query_explorer import NeoQueryParameters
from app.services.query_explorer import cap_lists, descriptions, neo_definition, parameters_for, path_row
from app.services.errors import APIError


class QueryExplorerTests(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.patch = patch('app.main.DatabaseConnections', return_value=self.db)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.client = TestClient(create_app(), raise_server_exceptions=False)
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    def test_catalog_lists_all_queries_without_database_reads(self):
        response = self.client.get('/api/consultas')
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()['data']
        self.assertEqual([q['id'] for q in data['mongodb']], list(range(1, 31)))
        self.assertEqual([q['id'] for q in data['neo4j']], list(range(1, 7)))
        self.db.mongo.__getitem__.assert_not_called()
        self.db.neo4j.session.assert_not_called()

    def test_no_arbitrary_text_ids_or_http_writes(self):
        for path in ('/api/consultas/mongodb/31', '/api/consultas/mongodb/0',
                     '/api/consultas/mongodb/1?query=dropDatabase',
                     '/api/consultas/neo4j/7?anio=2024',
                     '/api/consultas/neo4j/1?desde=2024&hasta=2024&cypher=DELETE'):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 422)
        self.assertEqual(self.client.post('/api/consultas/mongodb/1', json={'pipeline': [{'$out': 'x'}]}).status_code, 405)
        self.db.mongo.__getitem__.assert_not_called()
        self.db.neo4j.session.assert_not_called()

    def test_mongo_routes_dispatch_all_30_existing_ids(self):
        for identity in range(1, 31):
            with self.subTest(identity=identity), patch('app.services.query_explorer.execute_query', return_value=[{'registros': identity}]) as execute:
                response = self.client.get(f'/api/consultas/mongodb/{identity}')
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(response.json()['data']['id'], identity)
                self.assertEqual(execute.call_args.args[1]['id'], identity)
                self.assertEqual(response.json()['meta']['fuente'], 'mongodb')

    def test_specific_neo_parameters_required_before_query(self):
        invalid = ('/api/consultas/neo4j/1?desde=2024&hasta=2015',
                   '/api/consultas/neo4j/2?anio=2024',
                   '/api/consultas/neo4j/5?anio=2024&materia=MATEMATICA',
                   '/api/consultas/neo4j/3?anio=2024&materia=MATEMATICA&aprobado=false',
                   '/api/consultas/neo4j/4?cohorte_id=bad')
        for path in invalid:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 422)
        self.db.neo4j.session.assert_not_called()

    def test_all_original_cypher_files_and_false_parameter(self):
        catalog = descriptions()['neo4j']
        for query in catalog:
            definition, text = neo_definition(query['id'])
            self.assertIn('MATCH', text)
            self.assertEqual(definition[0], query['id'])
        definition, _ = neo_definition(3)
        params = parameters_for(definition, NeoQueryParameters(anio=2024, materia='MATEMATICA',
            aprobado=False, carrera_id='carrera:' + 'a' * 64))
        self.assertIs(params['aprobado'], False)
        with self.assertRaises(APIError):
            parameters_for(definition, NeoQueryParameters(anio=2024))

    def test_row_serialization_and_empty_results(self):
        class Node(dict):
            def __init__(self, label, **properties):
                super().__init__(**properties)
                self.labels = {label}
        evaluation = Node('Evaluacion', id='row', anio_ingreso=2024, aprobado=False)
        subject = Node('Materia', id='subject', nombre='MATEMATICA')
        row, paths = path_row({'p': SimpleNamespace(nodes=[evaluation, subject])})
        self.assertEqual(row['evaluacion'], 'row')
        self.assertIs(row['aprobado'], False)
        self.assertEqual(len(paths), 1)
        self.db.neo4j.session.return_value.__enter__.return_value.execute_read.return_value = ([], None, False)
        response = self.client.get('/api/consultas/neo4j/5?anio=2024')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['resultado'], [])

    def test_serialization_caps_keep_totals_and_do_not_mutate(self):
        source = {'registros': list(range(505)), 'total': 9999}
        result, capped = cap_lists(source)
        self.assertTrue(capped)
        self.assertEqual(len(result['registros']), 500)
        self.assertEqual(result['total'], 9999)
        self.assertEqual(len(source['registros']), 505)
