"""Carga aditiva: nunca reemplaza documentos existentes ni elimina registros."""
import csv
import hashlib
import json
from pathlib import Path

from pymongo import ASCENDING, MongoClient, UpdateOne
from pymongo.errors import PyMongoError

from .pipeline import analyze, normalize

DATABASE = 'usac_admisiones'
COLLECTION = 'evaluaciones'
INDEXES = (
    ([('anio_ingreso', ASCENDING), ('materia', ASCENDING)], 'anio_materia'),
    ([('aspirante.cohorte_id', ASCENDING)], 'aspirante_cohorte'),
    ([('fuente.sha256_archivo', ASCENDING)], 'fuente_sha256'),
)


def batches(documents, size):
    if not 1 <= size <= 10000:
        raise ValueError('batch-size debe estar entre 1 y 10000')
    batch = []
    for document in documents:
        batch.append(document)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch


def write_batch(collection, documents):
    operations = [UpdateOne({'_id': doc['_id']}, {'$setOnInsert': doc}, upsert=True)
                  for doc in documents]
    result = collection.bulk_write(operations, ordered=True)
    return {'insertadas': result.upserted_count, 'ya_existentes': result.matched_count}


def prepared_documents(input_dir, manifest):
    path = input_dir / manifest['archivo']
    # Una sola instantánea impide mezclar contenido si cambia el archivo al leerlo.
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != manifest['sha256']:
        raise ValueError('La fuente cambio despues del analisis')
    import io
    from .pipeline import ALIASES
    reader = csv.DictReader(io.StringIO(content.decode('utf-8-sig'), newline=''), strict=True)
    for number, row in enumerate(reader, 1):
        if None in row or any(value is None for value in row.values()):
            continue
        raw = {ALIASES.get(key.strip(), key.strip()): value for key, value in row.items()}
        document, errors, _ = normalize(raw, manifest['anio'], manifest['sha256'], number, path.name)
        if not errors:
            yield document


def load(input_dir, output_dir, batch_size=1000, dry_run=True, collection=None):
    if not 1 <= batch_size <= 10000:
        raise ValueError('batch-size debe estar entre 1 y 10000')
    if not dry_run and collection is None:
        raise ValueError('La carga real requiere una coleccion explicita')
    report = analyze(input_dir, output_dir)
    result = {'modo': 'dry-run' if dry_run else 'carga', 'estado': 'en_progreso',
              'base': DATABASE, 'coleccion': COLLECTION, 'batch_size': batch_size,
              'carga_ejecutada': not dry_run, 'por_anio': []}
    target = output_dir / 'carga.json'

    def save():
        target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    save()
    try:
        if not dry_run:
            for keys, name in INDEXES:
                collection.create_index(keys, name=name)
        for manifest in report['por_anio']:
            summary = {'anio': manifest['anio'], 'leidas': manifest['leidas'],
                       'validas': manifest['validas'], 'rechazadas': manifest['rechazadas'],
                       'preparadas': 0, 'lotes_confirmados': 0, 'insertadas': 0,
                       'ya_existentes': 0, 'cargadas': 0, 'lote_sin_confirmar': 0}
            result['por_anio'].append(summary)
            for batch in batches(prepared_documents(input_dir, manifest), batch_size):
                summary['preparadas'] += len(batch)
                if not dry_run:
                    summary['lote_sin_confirmar'] = len(batch)
                    save()
                    counts = write_batch(collection, batch)
                    summary['insertadas'] += counts['insertadas']
                    summary['ya_existentes'] += counts['ya_existentes']
                    summary['cargadas'] += counts['insertadas'] + counts['ya_existentes']
                    summary['lote_sin_confirmar'] = 0
                    summary['lotes_confirmados'] += 1
            if summary['preparadas'] != summary['validas']:
                raise ValueError('Conteo de documentos distinto al analisis')
            save()
        result['estado'] = 'completado'
    except Exception:
        result['estado'] = 'incompleto'
        save()
        # No imprimir excepciones del controlador: pueden contener datos originales.
        raise RuntimeError('Carga incompleta; consultar carga.json y reintentar con las mismas fuentes.') from None
    finally:
        save()
    return result


def run_load(args):
    if args.dry_run:
        return load(args.input_dir, args.output_dir, args.batch_size)
    # Esta ruta solo se alcanza con --execute; no inicializa Neo4j.
    from app.core.config import Settings
    settings = Settings()
    try:
        with MongoClient(host=settings.mongo_host, port=settings.mongo_port,
                         username=settings.mongo_root_username.get_secret_value(),
                         password=settings.mongo_root_password.get_secret_value(),
                         authSource=settings.mongo_auth_source,
                         timeoutMS=int(settings.db_timeout_seconds * 1000)) as client:
            return load(args.input_dir, args.output_dir, args.batch_size, False,
                        client[DATABASE][COLLECTION])
    except PyMongoError:
        raise RuntimeError('No se pudo completar la operacion MongoDB.') from None
