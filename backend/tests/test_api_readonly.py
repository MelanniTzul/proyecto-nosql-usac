"""Integración explícita: USAC_RUN_DB_TESTS=1. Solo operaciones de lectura."""
import json
import os
import time
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from neo4j import READ_ACCESS
from app.main import create_app


@unittest.skipUnless(os.environ.get('USAC_RUN_DB_TESTS') == '1', 'Requiere bases reales y autorización de lectura')
class ReadOnlyAPITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client=TestClient(create_app())
        cls.client.__enter__()
        cls.db=cls.client.app.state.databases
        cls.observed=[]
        cls.before=cls.counts()

    @classmethod
    def counts(cls):
        with cls.db.neo4j.session(database='neo4j',default_access_mode=READ_ACCESS) as session:
            nodes,edges=session.execute_read(lambda tx: (
                tx.run('MATCH (n) RETURN count(n) AS c').single()['c'],
                tx.run('MATCH ()-[r]->() RETURN count(r) AS c').single()['c']))
        return {'mongo_evaluaciones':cls.db.mongo['usac_admisiones']['evaluaciones'].count_documents({}),
                'neo4j_nodos':nodes,'neo4j_relaciones':edges}

    @classmethod
    def tearDownClass(cls):
        try:
            after=cls.counts()
            output=Path(__file__).resolve().parents[2]/'data/reports/etapa-5'
            output.mkdir(parents=True,exist_ok=True)
            (output/'verificacion-api.json').write_text(json.dumps({'antes':cls.before,'despues':after,'solicitudes':cls.observed},indent=2)+'\n')
            if cls.before!=after:
                raise AssertionError('Los conteos cambiaron durante pruebas de lectura')
        finally:
            cls.client.__exit__(None,None,None)

    def get(self,path,source=None):
        start=time.perf_counter();r=self.client.get(path)
        data=r.json() if 'application/json' in r.headers.get('content-type','') else None
        self.observed.append({'ruta':path,'status':r.status_code,'segundos':round(time.perf_counter()-start,3),
                              'filas':len(data['data']) if isinstance(data,dict) and isinstance(data.get('data'),list) else None})
        if isinstance(data,dict) and isinstance(data.get('data'),dict):
            payload=data['data']
            if 'nodes' in payload:
                self.observed[-1].update(nodos=len(payload['nodes']),relaciones=len(payload['edges']),truncado=data['meta']['truncado'])
            elif 'registros' in payload:
                self.observed[-1]['resumen']=payload
        self.assertEqual(r.status_code,200,r.text[:500])
        if source:self.assertEqual(data['meta']['fuente'],source)
        return data

    def test_health_swagger_and_schema(self):
        self.get('/api/health')
        self.assertEqual(self.get('/api/health/databases')['status'],'ok')
        self.get('/docs')
        self.assertEqual(len(self.get('/openapi.json')['paths']),11)

    def test_mongo_statistics_and_groups(self):
        stats=self.get('/api/estadisticas','mongodb')['data']
        self.assertEqual(stats['registros'],208453)
        self.assertEqual(stats['aprobados']+stats['no_aprobados'],stats['registros'])
        self.assertEqual(stats['registros_con_advertencias'],56147)
        annual=self.get('/api/estadisticas/aprobacion?desde=2024&hasta=2024','mongodb')['data']
        self.assertEqual(sum(r['registros'] for r in annual),13863)
        careers=self.get('/api/resultados/carreras?anio=2024','mongodb')['data']
        self.assertEqual(sum(r['registros'] for r in careers),13863)
        self.assertTrue(any(r['estado']=='recortada' for r in careers))
        provenance=self.get('/api/procedencia?anio=2024','mongodb')['data']
        self.assertEqual(sum(r['registros'] for r in provenance),13863)
        both=self.get('/api/resultados/ambas-materias?anio=2024&limite=3','mongodb')
        self.assertLessEqual(len(both['data']),3)
        self.assertTrue(all(set(r['materias'])=={'MATEMATICA','COMPUTACION'} for r in both['data']))

    def test_pagination_and_filters(self):
        base='/api/evaluaciones?anio=2024&materia=MATEMATICA&aprobado=false&limite=3'
        first=self.get(base,'mongodb')
        self.assertEqual(len(first['data']),3)
        self.assertTrue(all(r['anio_ingreso']==2024 and r['materia']=='MATEMATICA' and not r['aprobado'] for r in first['data']))
        second=self.get(base+'&cursor='+first['meta']['siguiente_cursor'],'mongodb')
        self.assertFalse({r['id'] for r in first['data']} & {r['id'] for r in second['data']})

    def test_graphs_and_catalogs(self):
        catalogs=self.get('/api/catalogos','mongodb')['data']
        self.assertEqual(catalogs['anios'],list(range(2015,2025)))
        career=next(c for c in catalogs['carreras'] if c['estado']=='completa' and c['carrera']=='INGENIERIA CIVIL')
        graph=self.get('/api/grafo?anio=2024&materia=MATEMATICA&aprobado=false&limite=5&carrera_id='+career['id'],'neo4j')
        self.assertTrue(graph['data']['nodes'])
        self.assertLessEqual(len(graph['data']['nodes']),500)
        self.assertLessEqual(len(graph['data']['edges']),800)
        ids={n['id'] for n in graph['data']['nodes']}
        self.assertTrue(all(e['source'] in ids and e['target'] in ids for e in graph['data']['edges']))
        self.assertEqual(len(ids),len(graph['data']['nodes']))
        evaluation_nodes=[n for n in graph['data']['nodes'] if n['tipo']=='Evaluacion']
        self.assertLessEqual(len(evaluation_nodes),5)
        self.assertTrue(all(n['properties']['anio_ingreso']==2024 and not n['properties']['aprobado'] for n in evaluation_nodes))
        aspirant=next(n for n in graph['data']['nodes'] if n['tipo']=='AspiranteCohorte')
        self.get('/api/grafo/aspirantes/'+aspirant['properties']['id']+'?limite=3','neo4j')
        absent=self.client.get('/api/grafo/aspirantes/2024:'+'0'*20)
        self.assertEqual(absent.status_code,404)

    def test_query_plans_and_maximum_graph(self):
        from app.services.graph_queries import SELECT_EVALUATIONS
        collection=self.db.mongo['usac_admisiones']['evaluaciones']
        plan=collection.find({'anio_ingreso':2024,'materia':'MATEMATICA','aprobado':False},{'_id':1}).sort('_id',1).limit(4).explain()
        self.assertTrue(plan['queryPlanner']['winningPlan'])
        params={'anio':2024,'materia':'MATEMATICA','aprobado':False,'carrera_id':None,'fetch':101}
        with self.db.neo4j.session(database='neo4j',default_access_mode=READ_ACCESS) as session:
            summary=session.execute_read(lambda tx: tx.run('EXPLAIN '+SELECT_EVALUATIONS,params).consume())
            self.assertEqual(summary.query_type,'r')
        graph=self.get('/api/grafo?anio=2024&limite=100','neo4j')
        self.assertLessEqual(len(graph['data']['nodes']),500)
        self.assertLessEqual(len(graph['data']['edges']),800)
        self.assertTrue(graph['meta']['truncado'])
