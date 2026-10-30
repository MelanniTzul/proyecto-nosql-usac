"""Pruebas de contrato en memoria: no conectan a MongoDB."""
import copy
import csv
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.etl.mongo import batches, load
from app.etl.pipeline import FIELDS
from test_etl import sample


class MemoryCollection:
    def __init__(self):
        self.documents = {}
        self.indexes = []
        self.batch_sizes = []
        self.fail_once = False

    def create_index(self, keys, name):
        self.indexes.append(name)

    def bulk_write(self, operations, ordered):
        self.batch_sizes.append(len(operations))
        inserted = matched = 0
        for operation in operations:
            assert operation._upsert
            document = operation._doc['$setOnInsert']
            assert operation._filter == {'_id': document['_id']}
            if document['_id'] in self.documents:
                matched += 1
            else:
                self.documents[document['_id']] = copy.deepcopy(document)
                inserted += 1
            if self.fail_once:
                self.fail_once = False
                raise RuntimeError('simulated partial write')
        return SimpleNamespace(upserted_count=inserted, matched_count=matched)


class LoaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.raw = self.root / 'raw'
        self.raw.mkdir()
        for year in range(2015, 2025):
            row = sample(year)
            row['anio_nacimiento'] = '1997'
            with (self.raw / f'pruebas_especificas_{year}.csv').open('w', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=FIELDS)
                writer.writeheader()
                writer.writerows([row, row, row])

    def test_two_full_runs_do_not_duplicate_or_replace(self):
        collection = MemoryCollection()
        first = load(self.raw, self.root / 'reports', 2, False, collection)
        originals = copy.deepcopy(collection.documents)
        second = load(self.raw, self.root / 'reports', 2, False, collection)
        self.assertEqual(len(collection.documents), 30)
        self.assertEqual(sum(s['insertadas'] for s in first['por_anio']), 30)
        self.assertEqual(sum(s['insertadas'] for s in second['por_anio']), 0)
        self.assertEqual(sum(s['ya_existentes'] for s in second['por_anio']), 30)
        self.assertEqual(collection.documents, originals)
        self.assertLessEqual(max(collection.batch_sizes), 2)
        doc = next(iter(originals.values()))
        self.assertEqual(doc['originales']['carrera_objetivo'], 'INGENIERIA MECANICA ')
        self.assertTrue(doc['calidad']['advertencias'])

    def test_dry_run_never_calls_collection(self):
        with patch('app.etl.mongo.MongoClient', side_effect=AssertionError('connection')):
            result = load(self.raw, self.root / 'reports', 2)
        self.assertEqual(result['estado'], 'completado')
        self.assertFalse(result['carga_ejecutada'])
        self.assertEqual(sum(s['preparadas'] for s in result['por_anio']), 30)
        self.assertEqual(sum(s['cargadas'] for s in result['por_anio']), 0)

    def test_partial_failure_then_retry(self):
        collection = MemoryCollection()
        collection.fail_once = True
        with self.assertRaises(RuntimeError):
            load(self.raw, self.root / 'reports', 2, False, collection)
        failed = json.loads((self.root / 'reports/carga.json').read_text())
        self.assertEqual(failed['estado'], 'incompleto')
        self.assertEqual(failed['por_anio'][0]['lote_sin_confirmar'], 2)
        result = load(self.raw, self.root / 'reports', 2, False, collection)
        self.assertEqual(result['estado'], 'completado')
        self.assertEqual(len(collection.documents), 30)

    def test_batch_limits(self):
        for size in (0, 10001):
            with self.assertRaises(ValueError):
                list(batches([], size))
        self.assertEqual(list(batches([1, 2, 3], 2)), [[1, 2], [3]])
