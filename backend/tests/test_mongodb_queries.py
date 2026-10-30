"""Contrato del catálogo: las consultas no escriben ni cambian las rutas existentes."""
import copy
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.queries.mongodb import execute_query, load_catalog, validate_query, verify_results


class MongoQueryTests(unittest.TestCase):
    def setUp(self):
        self.queries = load_catalog()
        self.db = SimpleNamespace(mongo=MagicMock(), settings=SimpleNamespace(api_query_timeout_seconds=10))

    def test_thirty_ids_and_distinct_objectives(self):
        self.assertEqual([q['id'] for q in self.queries], list(range(1, 31)))
        self.assertEqual(len({q['titulo'] for q in self.queries}), 30)
        self.assertEqual(sum(q['operacion'] == 'existing' for q in self.queries), 7)
        pipelines = [q['pipeline'] for q in self.queries if q['operacion'] == 'aggregate']
        self.assertEqual(len(pipelines), 22)
        self.assertEqual(len({str(p) for p in pipelines}), 22)

    def test_seven_existing_functions_are_reused(self):
        fixtures = {'evaluations': ([{'id': 'source'}], 'cursor'),
                    'statistics': {'registros': 3}, 'approval': [], 'careers': [],
                    'provenance': [], 'both_subjects': ([], False), 'catalogs': {'anios': []}}
        for query in self.queries:
            if query['operacion'] != 'existing':
                continue
            name = query['funcion']
            with self.subTest(function=name), patch('app.queries.mongodb.mongo_analytics.' + name, return_value=fixtures[name]) as function:
                execute_query(self.db, query)
                function.assert_called_once()
                self.assertIs(function.call_args.args[0], self.db)
        self.db.mongo.__getitem__.assert_not_called()

    def test_aggregate_target_timeout_and_original_spec_preserved(self):
        query = self.queries[23]
        before = copy.deepcopy(query)
        collection = self.db.mongo.__getitem__.return_value.__getitem__.return_value
        collection.aggregate.return_value = [{'ocurrencias_adicionales': 2}]
        self.assertEqual(execute_query(self.db, query), [{'ocurrencias_adicionales': 2}])
        self.db.mongo.__getitem__.assert_called_with('usac_admisiones')
        self.db.mongo.__getitem__.return_value.__getitem__.assert_called_with('evaluaciones')
        collection.aggregate.assert_called_once_with(query['pipeline'], maxTimeMS=60000, allowDiskUse=True)
        self.assertEqual(query, before)
        collection.insert_one.assert_not_called()
        collection.update_one.assert_not_called()
        collection.delete_many.assert_not_called()

    def test_count_uses_count_documents(self):
        collection = self.db.mongo.__getitem__.return_value.__getitem__.return_value
        collection.count_documents.return_value = 42
        self.assertEqual(execute_query(self.db, self.queries[1]), {'registros': 42})
        collection.count_documents.assert_called_once_with({}, maxTimeMS=60000)

    def test_writes_and_server_javascript_are_rejected(self):
        for operator in ('$out', '$merge', '$function', '$accumulator', '$where'):
            with self.subTest(operator=operator), self.assertRaises(ValueError):
                validate_query({'operacion': 'aggregate', 'pipeline': [{'$project': {'x': {operator: 'unsafe'}}}]})
        for query in ({'operacion': 'deleteMany'}, {'operacion': 'existing', 'funcion': 'drop'},
                      {'operacion': 'aggregate', 'pipeline': [{'$lookup': {}}]}):
            with self.assertRaises(ValueError):
                validate_query(query)

    def test_cross_query_invariants_detect_wrong_totals(self):
        good = [{'id': 2, 'estado': 'ok', 'resultado': {'registros': 5}},
                {'id': 4, 'estado': 'ok', 'resultado': [{'anio': 2024, 'registros': 5}]}]
        self.assertTrue(all(c['correcta'] for c in verify_results(good, 5)))
        bad = copy.deepcopy(good)
        bad[1]['resultado'][0]['registros'] = 4
        self.assertTrue(any(not c['correcta'] for c in verify_results(bad, 5)))

    def test_result_limits_preserve_metadata(self):
        with patch('app.queries.mongodb.mongo_analytics.evaluations', return_value=([{'id': 'a'}], 'next')):
            result = execute_query(self.db, self.queries[0])
            self.assertEqual(result['limite'], 10)
            self.assertEqual(result['siguiente_cursor'], 'next')
        with patch('app.queries.mongodb.mongo_analytics.both_subjects', return_value=([], True)):
            result = execute_query(self.db, self.queries[26])
            self.assertTrue(result['truncado'])
            self.assertEqual(result['limite'], 100)
