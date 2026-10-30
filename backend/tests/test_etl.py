import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from app.etl.pipeline import ALIASES, FIELDS, analyze, normalize


def sample(year=2024):
    return dict(zip(FIELDS, [f'{year-1}-09-05', 'F', '2005', 'MATEMATICA', '5',
                            str(year), 'APROBADO', 'INGENIERIA MECANICA ',
                            'GUATEMALA', 'GUATEMALA - CIUDAD ', 'PRIVADO',
                            'a' * (32 if year <= 2021 else 20)]))


class ETLTests(unittest.TestCase):
    def test_originals_ambiguity_and_deterministic_identity(self):
        raw = sample()
        doc, errors, warnings = normalize(raw, 2024, 'digest', 1, 'file.csv')
        self.assertFalse(errors)
        self.assertTrue(warnings)
        self.assertEqual(doc['originales']['carrera_objetivo'], 'INGENIERIA MECANICA ')
        self.assertEqual(doc['carrera']['estado_normalizacion'], 'recortada')
        self.assertEqual(doc['numero_fecha_evaluacion'], 5)
        self.assertEqual(doc['_id'], normalize(raw, 2024, 'digest', 1, 'renamed.csv')[0]['_id'])
        self.assertNotEqual(doc['_id'], normalize(raw, 2024, 'digest', 2, 'file.csv')[0]['_id'])
        self.assertEqual(raw, sample())

    def test_nulls(self):
        raw = sample()
        for field in ('sexo', 'anio_nacimiento'):
            raw[field] = 'SIN REGISTRO'
        raw['carrera_objetivo'] = 'NINGUNO'
        raw['municipio_institucion_educativa'] = 'SIN DATOS'
        doc, errors, _ = normalize(raw, 2024, 'd', 1, 'f')
        self.assertFalse(errors)
        self.assertIsNone(doc['aspirante']['anio_nacimiento'])
        self.assertIsNone(doc['carrera']['valor'])
        self.assertIsNone(doc['procedencia_educativa']['municipio'])

    def test_reject_invalid_values(self):
        for field, value in [('fecha_asignacion', '2023-02-30'),
                             ('fecha_asignacion', ''), ('anio_de_ingreso', '2023'),
                             ('anio_nacimiento', 'falso'), ('anio_nacimiento', '2025'),
                             ('aprobacion', 'QUIZAS'), ('materia', 'OTRA'),
                             ('numero_de_fecha_de_evaluacion', '6'),
                             ('correlativo_aspirante', '')]:
            with self.subTest(field=field, value=value):
                raw = sample()
                raw[field] = value
                self.assertTrue(normalize(raw, 2024, 'd', 1, 'f')[1])

    def test_all_files_reordered_aliases_duplicates_rejects_and_repeatability(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'raw'
            source.mkdir()
            hashes = {}
            for year in range(2015, 2025):
                raw = sample(year)
                raw['anio_nacimiento'] = '1997'
                raw['carrera_objetivo'] = 'INGENIERIA CIVIL'
                fields = list(reversed(FIELDS))
                inverse = {v: k for k, v in ALIASES.items()} if year >= 2022 else {}
                path = source / f'pruebas_especificas_{year}.csv'
                with path.open('w', newline='', encoding='utf-8-sig') as stream:
                    writer = csv.writer(stream)
                    writer.writerow([inverse.get(k, k) for k in fields])
                    writer.writerow([raw[k] for k in fields])
                    writer.writerow([raw[k] for k in fields])
                    writer.writerow(['broken'])
                hashes[path] = hashlib.sha256(path.read_bytes()).hexdigest()
            result = analyze(source, root / 'reports')
            self.assertEqual(result['totales']['leidas'], 30)
            self.assertEqual(result['totales']['validas'], 20)
            self.assertEqual(result['totales']['rechazadas'], 10)
            self.assertEqual(result['totales']['repeticiones_exactas'], 10)
            self.assertEqual(result['totales']['cargadas'], 0)
            self.assertEqual(result, analyze(source, root / 'reports'))
            self.assertEqual(len((root / 'reports/rechazos.jsonl').read_text().splitlines()), 10)
            for path, digest in hashes.items():
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)
            path.write_text('sexo,sexo\nM,F\n')
            with self.assertRaises(ValueError):
                analyze(source, root / 'bad-report')
            self.assertFalse((root / 'bad-report').exists())

    def test_missing_inputs_do_not_generate_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError):
                analyze(root, root / 'reports')
            self.assertFalse((root / 'reports').exists())
