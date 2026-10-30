"""Lectura reproducible, validación y reporte sin acceso a bases de datos."""
import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

VERSION = '1'
ROOT = Path(__file__).resolve().parents[3]
FIELDS = ('fecha_asignacion', 'sexo', 'anio_nacimiento', 'materia',
          'numero_de_fecha_de_evaluacion', 'anio_de_ingreso', 'aprobacion',
          'carrera_objetivo', 'departamento_institucion_educativa',
          'municipio_institucion_educativa', 'tipo_institucion_educativa',
          'correlativo_aspirante')
ALIASES = dict(zip(('numero_de_fecha_de_evaluaci', 'departamento_institucion_ed',
                   'municipio_institucion_'), FIELDS[4:5] + FIELDS[8:10]))
CAREERS = {'INGENIERIA AMBIENTAL', 'INGENIERIA CIVIL', 'INGENIERIA ELECTRICA',
           'INGENIERIA ELECTRONICA', 'INGENIERIA EN CIENCIAS Y SISTEMAS',
           'INGENIERIA INDUSTRIAL', 'INGENIERIA MECANICA',
           'INGENIERIA MECANICA ELECTRICA', 'INGENIERIA MECANICA INDUSTRIAL',
           'INGENIERIA QUIMICA', 'ITUGS', 'LICENCIATURA EN FISICA APLICADA',
           'LICENCIATURA EN MATEMATICA APLICADA'}
TRUNCATED_CAREERS = {'INGENIERIA EN CIENCIAS Y ', 'INGENIERIA MECANICA '}
DEPARTMENTS = set('ALTA VERAPAZ|BAJA VERAPAZ|CHIMALTENANGO|CHIQUIMULA|EL PROGRESO|ESCUINTLA|EXTRANJERO|GUATEMALA|HUEHUETENANGO|IZABAL|JALAPA|JUTIAPA|PETEN|QUEZALTENANGO|QUICHE|RETALHULEU|SACATEPEQUEZ|SAN MARCOS|SANTA ROSA|SOLOLA|SUCHITEPEQUEZ|TOTONICAPAN|ZACAPA'.split('|'))


def nullable(value, field):
    value = value.strip()
    markers = {'', 'SIN REGISTRO'}
    if field.endswith('institucion_educativa'):
        markers.add('SIN DATOS')
    if field == 'carrera_objetivo':
        markers.add('NINGUNO')
    return None if value in markers else value


def normalize(raw, year, digest, number, filename):
    """Devuelve documento, errores y advertencias. No infiere identidad personal."""
    values = {k: nullable(raw[k], k) for k in FIELDS}
    errors, warnings = [], []
    for field in ('anio_de_ingreso', 'anio_nacimiento', 'numero_de_fecha_de_evaluacion'):
        value = values[field]
        if value is None:
            if field != 'anio_nacimiento':
                errors.append(field + ': obligatorio')
        elif not re.fullmatch(r'[0-9]{1,4}', value):
            errors.append(field + ': entero invalido')
        else:
            values[field] = int(value)
    dt = None
    try:
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', values['fecha_asignacion'] or ''):
            raise ValueError
        dt = date.fromisoformat(values['fecha_asignacion'])
        if dt.year not in (year - 1, year):
            errors.append('fecha_asignacion: fuera de cohorte')
    except ValueError:
        errors.append('fecha_asignacion: fecha invalida')
    if values['anio_de_ingreso'] != year:
        errors.append('anio_de_ingreso: no coincide con archivo')
    n = values['numero_de_fecha_de_evaluacion']
    if isinstance(n, int) and n not in range(1, 6):
        errors.append('numero_de_fecha_de_evaluacion: fuera de 1..5')
    birth = values['anio_nacimiento']
    if isinstance(birth, int):
        if birth < 1900 or birth > (dt.year if dt else year):
            errors.append('anio_nacimiento: fuera de rango')
        elif dt and not 12 <= dt.year - birth <= 80:
            warnings.append('anio_nacimiento: edad aproximada atipica')
    catalogs = {
        'sexo': {'M', 'F'},
        'materia': {'MATEMATICA', 'COMPUTACION', 'MATEMATICA ITUGS'},
        'aprobacion': {'APROBADO', 'NO APROBADO'},
        'tipo_institucion_educativa': {'PRIVADO', 'PUBLICO', 'POR COOPERATIVA', 'MUNICIPAL'},
        'departamento_institucion_educativa': DEPARTMENTS,
    }
    for field, allowed in catalogs.items():
        if values[field] is None:
            if field in ('materia', 'aprobacion'):
                errors.append(field + ': obligatorio')
        elif values[field] not in allowed:
            errors.append(field + ': categoria desconocida')
    career = values['carrera_objetivo']
    career_state = 'ausente' if career is None else 'completa'
    if raw['carrera_objetivo'] in TRUNCATED_CAREERS:
        career_state = 'recortada'
        warnings.append('carrera_objetivo: valor recortado sin resolver')
    elif career is not None and career not in CAREERS:
        errors.append('carrera_objetivo: categoria desconocida')
    if year >= 2022 and values['municipio_institucion_educativa'] is not None:
        warnings.append('municipio: precision no garantizada por recorte de fuente')
    correlativo = values['correlativo_aspirante']
    if not correlativo or not re.fullmatch(r'[0-9a-f]{32}' if year <= 2021 else r'[0-9a-f]{20,23}', correlativo):
        errors.append('correlativo_aspirante: formato invalido')
    doc = {
        '_id': hashlib.sha256(f'{digest}:{number}'.encode()).hexdigest(),
        'anio_ingreso': values['anio_de_ingreso'], 'fecha_asignacion': values['fecha_asignacion'],
        'materia': values['materia'], 'numero_fecha_evaluacion': n,
        'aprobado': values['aprobacion'] == 'APROBADO',
        'aspirante': {'cohorte_id': f'{year}:{correlativo}', 'correlativo_original': correlativo,
                      'sexo': values['sexo'], 'anio_nacimiento': birth},
        'carrera': {'valor': career, 'estado_normalizacion': career_state},
        'procedencia_educativa': {k: values[k + '_institucion_educativa'] for k in ('departamento', 'municipio', 'tipo')},
        'originales': raw, 'calidad': {'advertencias': warnings},
        'fuente': {'archivo': filename, 'sha256_archivo': digest, 'numero_registro': number},
        'version_transformacion': VERSION,
    }
    return doc, errors, warnings


def analyze(input_dir, output_dir):
    paths = [input_dir / f'pruebas_especificas_{year}.csv' for year in range(2015, 2025)]
    missing = [p.name for p in paths if not p.is_file()]
    if missing:
        raise ValueError('Faltan CSV: ' + ', '.join(missing))
    # Verificar todos los encabezados antes de generar resultados.
    manifests = []
    for path in paths:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        with path.open(encoding='utf-8-sig', newline='') as stream:
            header = next(csv.reader(stream), [])
        canonical = [ALIASES.get(k.strip(), k.strip()) for k in header]
        if len(canonical) != len(set(canonical)) or set(canonical) != set(FIELDS):
            raise ValueError(f'Encabezado inesperado o duplicado: {path.name}')
        manifests.append((path, digest, canonical))
    output_dir.mkdir(parents=True, exist_ok=True)
    summaries, identities = [], defaultdict(lambda: defaultdict(set))
    with (output_dir / 'rechazos.jsonl').open('w', encoding='utf-8') as rejects:
        for path, digest, header in manifests:
            year = int(path.stem[-4:])
            summary = dict(anio=year, archivo=path.name, sha256=digest, leidas=0, validas=0,
                           rechazadas=0, cargadas=0, filas_con_advertencias=0, repeticiones_exactas=0)
            warnings_count, errors_count, seen = Counter(), Counter(), set()
            with path.open(encoding='utf-8-sig', newline='') as stream:
                reader = csv.reader(stream, strict=True)
                next(reader)
                for number, row in enumerate(reader, 1):
                    summary['leidas'] += 1
                    if len(row) != len(header):
                        errors, warnings = ['estructura: cantidad de columnas incorrecta'], []
                        raw = row
                    else:
                        raw = dict(zip(header, row))
                        fingerprint = tuple(raw[k] for k in FIELDS)
                        summary['repeticiones_exactas'] += fingerprint in seen
                        seen.add(fingerprint)
                        doc, errors, warnings = normalize(raw, year, digest, number, path.name)
                        if not errors:
                            identities[doc['aspirante']['cohorte_id']]
                            for field in ('sexo', 'anio_nacimiento'):
                                value = doc['aspirante'][field]
                                if value is not None:
                                    identities[doc['aspirante']['cohorte_id']][field].add(value)
                    if errors:
                        summary['rechazadas'] += 1
                        errors_count.update(errors)
                        rejects.write(json.dumps({'archivo': path.name, 'numero_registro': number,
                                                  'errores': errors, 'originales': raw}, ensure_ascii=False) + '\n')
                    else:
                        summary['validas'] += 1
                    summary['filas_con_advertencias'] += bool(warnings)
                    warnings_count.update(warnings)
            if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise ValueError(f'El archivo cambio durante el analisis: {path.name}')
            summary.update(advertencias=dict(warnings_count), errores=dict(errors_count))
            summaries.append(summary)
    report = {'modo': 'analisis_sin_escrituras_a_bases', 'version_transformacion': VERSION,
              'carga_ejecutada': False, 'por_anio': summaries,
              'totales': {k: sum(s[k] for s in summaries) for k in
                          ('leidas', 'validas', 'rechazadas', 'cargadas', 'filas_con_advertencias', 'repeticiones_exactas')},
              'identidad': {'alcance': 'anio + correlativo; no persona global',
                            'cohortes_observadas_validas': len(identities),
                            'cohortes_con_conflictos_demograficos': sum(any(len(v) > 1 for v in fields.values()) for fields in identities.values())}}
    (output_dir / 'reporte.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    with (output_dir / 'reporte.csv').open('w', encoding='utf-8', newline='') as stream:
        fields = ['anio', 'leidas', 'validas', 'rechazadas', 'cargadas', 'filas_con_advertencias', 'repeticiones_exactas']
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(summaries)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['analyze', 'load'])
    parser.add_argument('--input-dir', type=Path, default=ROOT / 'data/raw')
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'data/reports')
    parser.add_argument('--batch-size', type=int, default=1000)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--dry-run', action='store_true', default=True)
    mode.add_argument('--execute', action='store_false', dest='dry_run')
    args = parser.parse_args()
    if args.command == 'load':
        from .mongo import run_load
        try:
            report = run_load(args)
        except (ValueError, OSError, RuntimeError, UnicodeError, csv.Error):
            parser.exit(1, 'Carga incompleta; revisar fuentes, configuracion y carga.json.\n')
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return
    try:
        report = analyze(args.input_dir, args.output_dir)
    except (ValueError, OSError, UnicodeError, csv.Error) as exc:
        parser.exit(1, f'Analisis incompleto: {exc}\n')
    print(json.dumps(report['totales'], ensure_ascii=False, indent=2))
    print(f'Reportes: {args.output_dir.resolve()}')
