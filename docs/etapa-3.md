# Etapa 3: análisis ETL previo a la carga

Implementado el primer paso: lectura, normalización, validación y reportes.
El cargador MongoDB está implementado. Se ejecutaron dos cargas reales autorizadas
y se comprobó la idempotencia. Neo4j queda para otra fase.

Desde la raíz:

```bash
PYTHONPATH=backend .venv/bin/python -m app.etl analyze
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p test_etl.py -v
```

Se esperan exactamente los diez nombres `pruebas_especificas_2015.csv` hasta
`pruebas_especificas_2024.csv` en `data/raw/`. Se pueden indicar `--input-dir` y
`--output-dir`. El análisis no requiere credenciales ni bases activas.

Genera `data/reports/reporte.json`, `reporte.csv` y `rechazos.jsonl`.
Repetirlo reemplaza esos reportes generados; nunca modifica los CSV. Las huellas
SHA-256 antes y después de cada lectura permiten detectar cambios en la fuente.
Un fallo de lectura o estructura aborta con código 1: no debe interpretarse un
reporte previo o parcial como una ejecución completa.

## Reglas

Se valida el conjunto completo de encabezados y se rechazan columnas duplicadas,
faltantes o desconocidas. Tres alias explícitos resuelven los nombres abreviados;
las posiciones no tienen significado. Una fila con cantidad incorrecta de campos
se reporta como rechazada. Los registros se numeran desde 1 sin contar encabezados;
no son números de línea física si existe texto multilínea.

Se conservan todos los valores originales bajo nombres canónicos, sin recortar sus
espacios. La copia normalizada convierte vacíos y SIN REGISTRO a nulos; SIN DATOS
se aplica en procedencia y NINGUNO en carrera. Los encabezados originales permanecen
en los CSV inalterados. El documento normalizado se prepara en memoria; este paso
no exporta documentos ni los persiste en bases.

Fechas ISO válidas deben pertenecer al año de ingreso o al anterior. Año de ingreso
debe coincidir con el archivo. Nacimiento admite 1900 hasta el año de asignación;
una edad aproximada fuera de 12–80 produce advertencia, sin afirmar edad exacta.
Convocatorias admitidas: 1–5. Materias, aprobación, sexo, departamentos y tipos
educativos usan catálogos explícitos observados. Categorías desconocidas requieren
revisión y producen rechazo. Municipio no se valida contra un catálogo geográfico
externo: es una etiqueta publicada, que también puede contener una zona.

MATEMATICA ITUGS permanece separada. Las carreras recortadas se marcan sin resolver;
INGENIERIA MECANICA con espacio final no se confunde con la carrera completa.
Para 2022–2024 se advierte de precisión no garantizada en todos los municipios
informados: no se reconstruyen zonas ni nombres perdidos.

## Identidad y futura persistencia

Aspirante de cohorte significa año + correlativo, no persona global. El análisis
comprueba conflictos en sexo y nacimiento conocidos dentro de esa combinación.
Las carreras pertenecen a evaluaciones, porque pueden cambiar entre registros.

La clave documental es SHA-256 de `huella_archivo:numero_registro`. Identifica una
ocurrencia de fuente, no una persona ni un examen demostrado. Conserva repeticiones
exactas y permanece estable al renombrar archivos. Una fuente modificada tiene otra
huella y deberá revisarse como versión nueva antes de cargarla.

El cargador usa upsert por esa clave. Las pruebas de idempotencia usan una colección
en memoria; la verificación contra MongoDB real también se completó; ver resultados al final. La repetibilidad del análisis y las
claves sí están cubiertas por pruebas. La fecha de asignación se almacena como cadena ISO YYYY-MM-DD también en BSON:
es una fecha civil sin hora ni zona horaria, ordenable y agrupable por año.

La futura proyección incluye AspiranteCohorte, Evaluacion, Materia, Carrera,
Cohorte, LocalidadEducativa, Departamento y TipoInstitucion. Cada evaluación enlaza
su aspirante de cohorte, materia, carrera informada, cohorte y procedencia educativa.
LocalidadEducativa se identifica por departamento y etiqueta observada. No representa
una escuela concreta. No se crean relaciones para datos nulos ni personas globales.
La proyección reutilizará los identificadores documentales y usará MERGE.

## Conteos

Válidas + rechazadas = leídas. Válida significa compatible con estas reglas, no
información completa o identidad verificada. Las advertencias no rechazan filas;
una fila puede tener varias. Repeticiones exactas cuenta ocurrencias adicionales
iguales en las doce columnas originales dentro de cada archivo. No se eliminan.
Cargadas es cero y `carga_ejecutada` es falso: no es un conteo consultado a las bases.
Los rechazos incluyen originales y razones. Los reportes generados se excluyen de
Git para evitar versionar datos y resultados locales.

Las pruebas verifican ambos esquemas con columnas invertidas, nulos, errores,
ambigüedad, preservación de CSV, claves estables, repeticiones, entradas faltantes,
encabezados duplicados y repetibilidad de los reportes. No acceden a bases.

## Cargador MongoDB

Simulación, sin conexiones, credenciales ni escrituras a MongoDB:

```bash
PYTHONPATH=backend .venv/bin/python -m app.etl load --dry-run --batch-size 1000
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_etl*.py' -v
```

`load` sin opciones también es simulación. El comando de carga real, ejecutado con autorización explícita, es:

```bash
PYTHONPATH=backend .venv/bin/python -m app.etl load --execute --batch-size 1000
```

Destino fijo: base `usac_admisiones`, colección `evaluaciones`. El cliente lee las
credenciales existentes de Settings y no inicializa Neo4j. Los lotes admiten 1–10000
documentos. Antes de escribir se ejecuta el análisis completo; las filas rechazadas
se excluyen y quedan en rechazos.jsonl. Cada archivo se verifica contra la huella del
análisis y se transforma desde una instantánea en memoria (un archivo a la vez).

Cada operación es UpdateOne por `_id`, con `$setOnInsert` y `upsert=True`. Por tanto,
repetir las mismas fuentes conserva los documentos existentes, sus originales y
advertencias. Una nueva versión del transformador no actualiza silenciosamente los
documentos previos: requeriría diseñar una migración explícita. No se deduplican las
repeticiones originales dentro del CSV. La protección de unicidad es el índice `_id`
automático de MongoDB; no se usa el correlativo como clave única.

Índices secundarios no únicos creados aditivamente al ejecutar carga real:

| Nombre | Campos | Uso |
| --- | --- | --- |
| anio_materia | anio_ingreso, materia | Filtros por cohorte y materia |
| aspirante_cohorte | aspirante.cohorte_id | Registros del correlativo dentro del año |
| fuente_sha256 | fuente.sha256_archivo | Trazabilidad de un archivo |

Si ya existe un índice incompatible, se informa fallo sin borrar ni reemplazarlo.

Formato del documento:

| Campo | Tipo BSON / significado |
| --- | --- |
| _id | string SHA-256 de huella de fuente + número de registro |
| anio_ingreso | entero |
| fecha_asignacion | string de fecha ISO |
| materia | string del catálogo observado |
| numero_fecha_evaluacion | entero 1–5, no intento inferido |
| aprobado | booleano |
| aspirante | objeto con cohorte_id y correlativo_original strings, sexo string/null, anio_nacimiento entero/null |
| carrera | objeto con valor string/null y estado_normalizacion |
| procedencia_educativa | objeto con departamento, municipio y tipo string/null |
| originales | las doce columnas canónicas con valores originales string |
| calidad.advertencias | lista de strings |
| fuente | archivo, sha256_archivo y numero_registro |
| version_transformacion | string |

`carga.json` se genera además de los reportes del análisis. Por año distingue leídas,
válidas, rechazadas, preparadas, insertadas, ya existentes, cargadas (insertadas +
existentes confirmadas), lotes confirmados y tamaño del lote sin confirmar.
En simulación no se puede conocer cuántos documentos existen en MongoDB: insertadas,
ya_existentes y cargadas quedan en cero. Preparadas muestra lo que se enviaría.
`reporte.json` y `reporte.csv` describen solo el análisis previo, con cargadas=0;
el resultado de carga pertenece exclusivamente a `carga.json`.

No existe transacción global: un fallo puede dejar inserciones parciales. Se guarda
estado incompleto y el tamaño del lote sin confirmar, sin atribuirle resultados
que el servidor no confirmó. Repetir la carga completa con las mismas fuentes es
seguro gracias al upsert. No se imprimen excepciones del controlador que podrían
incluir documentos o credenciales. Los reportes se sobrescriben entre ejecuciones;
copiar su directorio si se necesita conservar el historial.

Las nueve pruebas locales incluyen dos cargas completas sobre una colección en
memoria, lotes limitados, preservación exacta, recuperación tras inserción parcial
y simulación sin cliente. Validan las operaciones PyMongo construidas y el contrato
del cargador; no sustituyen una futura prueba de integración con MongoDB real.


## Cargas reales autorizadas: 30 de octubre de 2026

Se ejecutaron dos cargas exclusivamente en `usac_admisiones.evaluaciones`, con
lotes de hasta 1000 documentos (213 lotes por ejecución).

| Resultado | Primera carga | Segunda carga |
| --- | ---: | ---: |
| Insertadas | 208453 | 0 |
| Ya existentes | 0 | 208453 |
| Rechazadas | 0 | 0 |
| Documentos reales al finalizar | 208453 | 208453 |
| Lotes sin confirmar | 0 | 0 |

Ambas ejecuciones terminaron completadas. El conteo real se consultó directamente
a MongoDB después de cada ejecución. Los conteos por año coinciden con los diez
CSV. La segunda ejecución confirmó que repetir las mismas fuentes no añade
ocurrencias ni reemplaza documentos. Las 834 repeticiones originales permanecen.

Se verificaron los índices `_id_`, `anio_materia`, `aspirante_cohorte` y
`fuente_sha256`. `_id_` impone unicidad; los secundarios son no únicos.
Los reportes completos están en `data/reports/primera-carga/`,
`data/reports/segunda-carga/` y `data/reports/verificacion-mongodb.json`.
Son artefactos locales excluidos de Git. No se eliminaron ni reemplazaron bases o
colecciones, no se ejecutaron commits/merges/push y no se implementó Neo4j.
