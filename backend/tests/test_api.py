"""Contratos HTTP, límites, filtros y fallos sin conexiones a bases reales."""
import copy
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from pymongo.errors import ExecutionTimeout, ServerSelectionTimeoutError
from neo4j.exceptions import ServiceUnavailable

from app.main import create_app
from app.core.config import HTTPSettings
from app.models.analytics import EvaluationFilters
from app.services import mongo_analytics
from app.services.graph_queries import serialize
from test_etl import sample
from app.etl.pipeline import normalize


class APITests(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.db.settings.api_query_timeout_seconds = 10
        self.connections = patch('app.main.DatabaseConnections', return_value=self.db)
        self.connections.start()
        self.addCleanup(self.connections.stop)
        self.client = TestClient(create_app(), raise_server_exceptions=False)
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    def test_swagger_and_openapi(self):
        self.assertEqual(self.client.get('/docs').status_code, 200)
        spec = self.client.get('/openapi.json').json()
        self.assertEqual(len(spec['paths']), 11)
        self.assertIn('422',spec['paths']['/api/evaluaciones']['get']['responses'])
        self.assertEqual(self.client.get('/api/health').json(), {'status':'ok','service':'usac-admisiones-api'})

    def test_bad_filters_never_call_database(self):
        urls = ['/api/evaluaciones?anio=2014', '/api/evaluaciones?limite=101',
                '/api/evaluaciones?limite=0', '/api/evaluaciones?materia=OTRA',
                '/api/evaluaciones?aprobado=quizas', '/api/evaluaciones?desconocido=1',
                '/api/estadisticas/aprobacion?desde=2024&hasta=2015', '/api/grafo',
                '/api/grafo?anio=2024&carrera_id=inyeccion', '/api/procedencia',
                '/api/grafo/aspirantes/global', '/api/evaluaciones?cursor='+'a'*1025]
        for url in urls:
            with self.subTest(url=url[:90]):
                r=self.client.get(url)
                self.assertEqual(r.status_code,422,r.text)
                self.assertEqual(r.json()['status'],'error')
        self.db.mongo.__getitem__.assert_not_called()
        self.db.neo4j.session.assert_not_called()

    def test_malformed_cursor(self):
        for value in ('!!!!','W10=','e30='):
            self.assertEqual(self.client.get('/api/evaluaciones',params={'cursor':value}).status_code,422)
        self.db.mongo.__getitem__.assert_not_called()

    def test_cursor_pages_filter_binding_and_projection(self):
        docs = [normalize(sample(),2024,'d',n,'f')[0] for n in (1,2,3)]
        docs.sort(key=lambda d:d['_id'])
        self.db.mongo.__getitem__.return_value.__getitem__.return_value.find.return_value.sort.return_value.limit.return_value.max_time_ms.side_effect = [copy.deepcopy(docs[:2]),copy.deepcopy(docs[1:2])]
        first=self.client.get('/api/evaluaciones?anio=2024&limite=1')
        self.assertEqual(first.status_code,200,first.text)
        cursor=first.json()['meta']['siguiente_cursor']
        self.assertTrue(cursor)
        self.assertNotIn('originales',first.json()['data'][0])
        self.assertNotIn('correlativo_original',first.json()['data'][0]['aspirante'])
        second=self.client.get('/api/evaluaciones',params={'anio':2024,'limite':1,'cursor':cursor})
        self.assertEqual(second.status_code,200,second.text)
        self.assertNotEqual(first.json()['data'][0]['id'],second.json()['data'][0]['id'])
        self.assertIsNone(second.json()['meta']['siguiente_cursor'])
        self.assertEqual(self.client.get('/api/evaluaciones',params={'anio':2023,'cursor':cursor}).status_code,422)
        find=self.db.mongo.__getitem__.return_value.__getitem__.return_value.find
        self.assertIn('$gt',find.call_args.args[0]['_id'])

    def test_empty_statistics_and_zero_denominator(self):
        self.db.mongo.__getitem__.return_value.__getitem__.return_value.aggregate.return_value=[]
        r=self.client.get('/api/estadisticas?anio=2024')
        self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(r.json()['data']['registros'],0)
        self.assertIsNone(r.json()['data']['porcentaje_aprobacion'])
        self.db.neo4j.session.assert_not_called()

    def test_database_errors_are_safe_and_independent(self):
        coll=self.db.mongo.__getitem__.return_value.__getitem__.return_value
        for error,status in [(ServerSelectionTimeoutError('secret-test'),503),(ExecutionTimeout('secret-test'),504)]:
            coll.aggregate.side_effect=error
            r=self.client.get('/api/estadisticas')
            self.assertEqual(r.status_code,status,r.text)
            self.assertNotIn('secret-test',r.text)
        self.db.neo4j.session.side_effect=ServiceUnavailable('secret-neo')
        r=self.client.get('/api/grafo?anio=2024')
        self.assertEqual(r.status_code,503,r.text)
        self.assertNotIn('secret-neo',r.text)
        # El fallo Neo4j no impide recuperar estadísticas MongoDB.
        coll.aggregate.side_effect=None
        coll.aggregate.return_value=[]
        self.assertEqual(self.client.get('/api/estadisticas').status_code,200)

    def test_unexpected_error_and_not_found(self):
        with patch('app.api.analytics.mongo_analytics.catalogs',side_effect=RuntimeError('private-secret')):
            r=self.client.get('/api/catalogos')
            self.assertEqual(r.status_code,500)
            self.assertNotIn('private-secret',r.text)
        self.assertEqual(self.client.get('/unknown').status_code,404)
        self.assertEqual(self.client.post('/api/estadisticas').status_code,405)

    def test_cors_origins_and_preflight(self):
        allowed=self.client.options('/api/evaluaciones',headers={'Origin':'http://localhost:5173','Access-Control-Request-Method':'GET'})
        self.assertEqual(allowed.status_code,200)
        self.assertEqual(allowed.headers['access-control-allow-origin'],'http://localhost:5173')
        denied=self.client.options('/api/evaluaciones',headers={'Origin':'https://unknown.example','Access-Control-Request-Method':'GET'})
        self.assertEqual(denied.status_code,400)
        self.assertNotIn('access-control-allow-origin',denied.headers)
        for origin in ('*','http://host/path','http://user:pass@host','http://host:bad'):
            with self.assertRaises(ValueError):
                HTTPSettings(_env_file=None,cors_origins=[origin])


class Node(dict):
    def __init__(self,kind,identity):
        super().__init__(id=identity)
        self.labels={kind,'USACAdmision'}


class GraphSerializerTests(unittest.TestCase):
    def test_caps_deduplication_and_no_dangling_edges(self):
        a=Node('Evaluacion','a');b=Node('Materia','b');c=Node('Materia','c')
        r1=SimpleNamespace(start_node=a,end_node=b,type='DE_MATERIA')
        r2=SimpleNamespace(start_node=a,end_node=c,type='DE_MATERIA')
        path=SimpleNamespace(relationships=[r1,r1,r2])
        data,capped=serialize([path],max_nodes=2,max_edges=1)
        self.assertTrue(capped)
        self.assertEqual(len(data['nodes']),2)
        self.assertEqual(len(data['edges']),1)
        ids={n['id'] for n in data['nodes']}
        self.assertTrue(all(e['source'] in ids and e['target'] in ids for e in data['edges']))
        self.assertEqual(data,serialize([path],max_nodes=2,max_edges=1)[0])

    def test_cursor_is_bound_to_false_filter(self):
        f=EvaluationFilters(anio=2024,aprobado=False)
        cursor=mongo_analytics.encode_cursor('a'*64,f)
        self.assertEqual(mongo_analytics.decode_cursor(cursor,f),'a'*64)
        with self.assertRaises(Exception):
            mongo_analytics.decode_cursor(cursor,EvaluationFilters(anio=2024,aprobado=True))
