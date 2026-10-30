import copy
import unittest
import tempfile
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.etl.pipeline import normalize
from test_etl import sample
from app.graph.projector import Inventory, key, project
from app.graph.loader import merged_batch, schema_statements, write_graph


def document(year=2024, number=1):
    return normalize(sample(year), year, f'digest-{year}', number, 'file.csv')[0]


class Result(list):
    def consume(self):
        return None


class Transaction:
    def __init__(self):
        self.nodes, self.edges = {}, set()

    def run(self, query, rows):
        if 'RETURN n.id' in query:
            return Result({'id': row['id'], 'labels': ['USACAdmision'],
                           'props': self.nodes[row['id']]} for row in rows if row['id'] in self.nodes)
        if 'ON CREATE SET' in query:
            for row in rows:
                self.nodes.setdefault(row['id'], copy.deepcopy(row['props']))
        else:
            for row in rows:
                self.edges.add((row['source'], row['type'], row['target']))
        return Result()


class GraphTests(unittest.TestCase):
    def test_cohort_not_global(self):
        first, second = document(), document(2023)
        second['aspirante']['correlativo_original'] = first['aspirante']['correlativo_original']
        second['aspirante']['cohorte_id'] = '2023:' + first['aspirante']['correlativo_original']
        inv = Inventory()
        inv.add(first)
        inv.add(second)
        self.assertEqual(inv.report()['nodos']['AspiranteCohorte'], 2)

    def test_ambiguous_categories_and_no_null_nodes(self):
        raw = document()
        recortada = project(raw)
        raw['carrera']['estado_normalizacion'] = 'completa'
        completa = project(raw)
        ids = lambda g: [n['id'] for n in g['nodes'] if n['label']=='CarreraObservada']
        self.assertNotEqual(ids(recortada), ids(completa))
        raw['carrera']['valor'] = None
        raw['procedencia_educativa'] = dict.fromkeys(('departamento','municipio','tipo'))
        graph = project(raw)
        self.assertEqual(len(graph['nodes']), 4)
        self.assertEqual(len(graph['edges']), 3)

    def test_conflict_and_malformed_identity(self):
        inv = Inventory()
        first = document()
        inv.add(first)
        other = document(number=2)
        other['aspirante']['sexo'] = 'M'
        with self.assertRaises(ValueError):
            inv.add(other)
        first['aspirante']['cohorte_id'] = 'global'
        with self.assertRaises(ValueError):
            project(first)

    def test_repeat_and_replay_after_checkpoint_loss(self):
        inv, tx = Inventory(), Transaction()
        graphs = [inv.add(document(number=i)) for i in (1,2)]
        graph = merged_batch(graphs, inv)
        write_graph(tx, graph)
        before = copy.deepcopy((tx.nodes,tx.edges))
        write_graph(tx, graph)
        self.assertEqual(before,(tx.nodes,tx.edges))
        self.assertEqual(inv.report()['nodos']['Evaluacion'],2)
        self.assertEqual(len(schema_statements()),9)

    def test_existing_conflict_stops_before_write(self):
        inv, tx = Inventory(), Transaction()
        graph = merged_batch([inv.add(document())],inv)
        tx.nodes[document()['_id']] = {'aprobado':'incompatible'}
        with self.assertRaises(ValueError):
            write_graph(tx,graph)
        self.assertFalse(tx.edges)

    def test_keys_unambiguous_and_originals_unchanged(self):
        self.assertNotEqual(key('x','a:b','c'),key('x','a','b:c'))
        raw = document()
        before = copy.deepcopy(raw)
        project(raw)
        self.assertEqual(raw,before)

    def test_cli_dry_run_never_opens_neo4j(self):
        from app.graph.__main__ import main
        with tempfile.TemporaryDirectory() as directory:
            client = MagicMock()
            collection = client.return_value.__enter__.return_value.__getitem__.return_value.__getitem__.return_value
            collection.find.return_value.sort.return_value.batch_size.return_value = [document()]
            with patch.object(sys, 'argv', ['graph', '--dry-run', '--output-dir', directory]), \
                 patch('app.graph.__main__.Settings') as settings, \
                 patch('app.graph.__main__.MongoClient', client), \
                 patch('neo4j.GraphDatabase.driver', side_effect=AssertionError('Neo4j connection')), \
                 patch('builtins.print'):
                settings.return_value.neo4j_database = 'neo4j'
                main()
            self.assertTrue((Path(directory) / 'simulacion.json').exists())

    def test_execute_rejects_unapproved_database_before_connection(self):
        from app.graph.__main__ import execute
        from types import SimpleNamespace
        with patch('neo4j.GraphDatabase.driver', side_effect=AssertionError('connection')):
            with self.assertRaisesRegex(ValueError, 'Destino no autorizado'):
                execute(None, SimpleNamespace(neo4j_database='otra_base'), None, None, {})
