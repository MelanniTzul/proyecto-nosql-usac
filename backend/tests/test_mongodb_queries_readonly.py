"""Integración optativa del catálogo completo: solo lecturas reales."""
import os
import unittest

from pymongo import timeout
from app.core.config import Settings
from app.database.connections import DatabaseConnections
from app.queries.mongodb import execute_query, load_catalog, verify_results


@unittest.skipUnless(os.environ.get('USAC_RUN_DB_TESTS') == '1', 'Requiere MongoDB real en modo lectura')
class MongoCatalogReadOnlyTests(unittest.TestCase):
    def test_thirty_queries_and_cross_query_invariants(self):
        connections = DatabaseConnections(Settings())
        try:
            collection = connections.mongo['usac_admisiones']['evaluaciones']
            total = collection.count_documents({})
            self.assertGreater(total, 0)
            results = []
            for query in load_catalog():
                with self.subTest(id=query['id']), timeout(60):
                    result = execute_query(connections, query)
                    results.append({'id': query['id'], 'estado': 'ok', 'resultado': result})
            self.assertEqual(len(results), 30)
            for check in verify_results(results, total):
                self.assertTrue(check['correcta'], check['comprobacion'])
            self.assertEqual(collection.count_documents({}), total)
        finally:
            connections.close()
