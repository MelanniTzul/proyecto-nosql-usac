# Etapa 4: proyección MongoDB → Neo4j

Implementación validada en `feature/neo4j-grafos`: 208453 evaluaciones,
265293 nodos y 1222881 relaciones. Las dos pasadas completas finalizaron
sin duplicados ni cambios de propiedades entre ejecuciones.

## Identidad y modelo

Evaluacion representa una ocurrencia de fuente, no un examen único demostrado.
Su id es el `_id` de MongoDB. AspiranteCohorte conserva `aspirante.cohorte_id`
(año:correlativo), nunca una persona global ni un vínculo entre años. Se verifican
conflictos de propiedades compartidas antes de escribir.

| Nodo | Clave | Propiedades |
| --- | --- | --- |
| Evaluacion | _id MongoDB | año, fecha ISO, convocatoria, aprobado, advertencias, fuente, versión |
| AspiranteCohorte | año:correlativo | año, correlativo, sexo, nacimiento conocido |
| Cohorte | año como string | anio |
| Materia | hash del nombre | nombre |
| CarreraObservada | hash de valor + estado | nombre, estado_normalizacion |
| LocalidadEducativa | hash de departamento + etiqueta + precisión | nombre_observado, precision_fuente |
| Departamento | hash del nombre | nombre |
| TipoInstitucion | hash del tipo | nombre |

Hashes: prefijo de entidad + SHA-256 de lista JSON UTF-8 sin espacios, orden de
componentes fijo. No se infieren identidades personales. Los atributos originales
completos permanecen en MongoDB, recuperables por id. Los nodos llevan además la
etiqueta USACAdmision. Nulos no producen nodos ni relaciones.

Relaciones dirigidas: AspiranteCohorte → TIENE_REGISTRO → Evaluacion;
Evaluacion → EN_COHORTE → Cohorte; Evaluacion → DE_MATERIA → Materia;
Evaluacion → ASPIRA_A → CarreraObservada; Evaluacion → PROCEDENCIA_EDUCATIVA →
LocalidadEducativa; LocalidadEducativa → EN_DEPARTAMENTO → Departamento;
Evaluacion → TIPO_INSTITUCION → TipoInstitucion.

Resultado, convocatoria, sexo y nacimiento son atributos; materia y carrera son
categorías compartidas útiles para recorridos. No se inventan escuelas ni residencia.
Carreras recortadas se separan de completas aunque coincida su nombre normalizado.
Localidades desde 2022 tienen precisión no garantizada; no se reconstruyen zonas.
MATEMATICA ITUGS permanece separada. Fecha de asignación no es fecha del examen,
convocatoria no es intento y aprobar ambas materias no prueba admisión definitiva.

## Ejecutar pruebas y simulación

Desde la raíz, con dependencias existentes:

```bash
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p test_graph.py -v
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_etl*.py' -v
PYTHONPATH=backend .venv/bin/python -m app.graph --dry-run
```

Sin opciones también es dry-run. Lee exclusivamente usac_admisiones.evaluaciones,
ordena por el índice _id y no abre cliente Neo4j. Settings sigue requiriendo las
variables de configuración existentes, incluso las de Neo4j. El reporte local está
en data/reports/neo4j/simulacion.json, excluido de Git. `--output-dir` cambia su ruta.
Un error aborta con código 1 sin publicar un nuevo reporte completo; un reporte
anterior puede permanecer. No interpretar ese archivo como resultado de un intento
fallido. La simulación mantiene el inventario de nodos y relaciones en memoria;
la carga transmite lotes, no todo el grafo en una transacción.

## Cargador y reanudación

Después de autorización explícita:

```bash
PYTHONPATH=backend .venv/bin/python -m app.graph --execute --batch-size 500
PYTHONPATH=backend .venv/bin/python -m app.graph --execute --resume --batch-size 500
```

Destino: exclusivamente `neo4j`; el cargador rechaza otro valor de
Settings.neo4j_database antes de conectar. El reporte muestra el destino. Antes del DDL se inspeccionan nodos con etiquetas del modelo, restricciones
e índices. Colisiones con nodos ajenos o propiedades incompatibles abortan. Se crean
restricciones únicas sobre id en las ocho etiquetas y un índice compuesto en
Evaluacion(anio_ingreso, aprobado), siempre con IF NOT EXISTS. Una restricción
incompatible o duplicados preexistentes pueden impedir su creación: no se borran.
Las restricciones tienen alcance de etiqueta, incluyendo datos previos con esa
etiqueta; por eso la inspección previa es necesaria.

Un escritor, lotes de 1–2000 registros, por defecto 500. UNWIND parametrizado,
MERGE por id, propiedades solo ON CREATE y relaciones MERGE entre extremos ligados.
Cada lote es una transacción del controlador; una excepción revierte ese lote.
Los reintentos automáticos están desactivados: un fallo detiene la ejecución.
La carga nunca actualiza documentos MongoDB, elimina datos ni reemplaza propiedades
existentes. Puede añadir relaciones faltantes de la proyección aprobada.

Checkpoint local: huella de proyección, versión, host, puerto, base y último _id
confirmado. Se escribe con reemplazo atómico después del commit. Perderlo permite
repetir el lote sin duplicarlo; --resume exige misma fuente y destino. Si se recrea
la base Neo4j, no reutilizar el checkpoint: repetir desde el inicio. Un --execute
sin --resume reprocesa todo. El checkpoint representa progreso, no un respaldo.

La fuente se verifica de nuevo antes de los lotes y se contrastan sus propiedades
al cargar. No existe una instantánea distribuida MongoDB/Neo4j: no ejecutar cargas
concurrentes ni modificar la fuente durante el proceso. Una fuente modificada puede
provocar fallo tras algunos lotes; el grafo parcial no se elimina. Verificar el
manifiesto y reintentar con las mismas fuentes. DDL puede quedar creado si falla
una etapa posterior. No hay rollback global.

## Consultas

Seis archivos en consultas/neo4j:

1. 01_aprobacion: porcentaje por cohorte y materia; parámetros desde y hasta.
2. 02_carreras: registros/aprobaciones por carrera y estado; anio, materia.
3. 03_visualizacion: caminos con filtros; anio, materia, carrera_id, aprobado.
4. 04_aspirante: registros de una cohorte individual; cohorte_id.
5. 05_ambas_materias: cohortes individuales con aprobación en ambas; anio.
6. 06_procedencia: recorrido localidad → departamento y tipo educativo; anio.

Ejemplos: anio=2024, desde=2015, hasta=2024, materia='MATEMATICA', aprobado=true.
Para carrera_id usar `key('carrera', valor, estado)` del proyector o consultar el id
del nodo por nombre y estado. cohorte_id es el valor de MongoDB, sin alterarlo.
Enviar parámetros separados del texto Cypher. La visualización limita a 100 caminos;
las consultas agregadas cuentan registros incluyendo repeticiones originales.
No usar recorridos ilimitados ni intentar visualizar el grafo completo.

Las seis consultas pasaron EXPLAIN y ejecución real de lectura tanto en el lote
de prueba como en el grafo completo, usando filtros de año y límites.
El DDL documentado también se ejecutó. La medición con PROFILE del grafo completo
sigue pendiente.
Las restricciones respaldan los MERGE por id; las búsquedas por categorías parten
de sus nodos y el índice compuesto ayuda a filtros por año/resultado.

## Verificación realizada

Ocho pruebas del grafo y nueve del ETL correctas. El CLI dry-run se prueba con
un controlador Neo4j que falla si se invoca; no se abre esa conexión. Las de escritura usan un doble de
transacción en memoria: prueban la construcción de operaciones, repetición tras
pérdida de checkpoint y rechazo de conflictos; no demuestran rollback, sintaxis
Cypher ni comportamiento de un servidor real. Las cargas completas verificaron las operaciones contra el servidor real.
No se provocaron fallos de red ni se hizo una prueba real de interrupción
y reanudación: ese escenario sigue cubierto solo parcialmente por pruebas locales.

La simulación real completó 208453 documentos sin conflictos. Huella:
8e861123331cc31fb4c63f853bafcc438deaba7ddee84d956b0195e52db70de0.

| Nodo | Cantidad |
| --- | ---: |
| Evaluacion | 208453 |
| AspiranteCohorte | 56337 |
| Cohorte | 10 |
| Materia | 3 |
| CarreraObservada | 15 |
| LocalidadEducativa | 448 |
| Departamento | 23 |
| TipoInstitucion | 4 |

| Relación | Cantidad |
| --- | ---: |
| TIENE_REGISTRO | 208453 |
| EN_COHORTE | 208453 |
| DE_MATERIA | 208453 |
| ASPIRA_A | 188178 |
| PROCEDENCIA_EDUCATIVA | 204448 |
| EN_DEPARTAMENTO | 448 |
| TIPO_INSTITUCION | 204448 |

Después de una carga autorizada, comparar estos conteos por etiqueta/tipo, revisar
una muestra por id contra MongoDB y repetir la carga: no deben aumentar los conteos.
Confirmar también propiedades de fuente y carreras recortadas. Si hay información
previa de otro origen, contar solo la proyección del proyecto.


## Prueba real autorizada de 500 evaluaciones

Destino confirmado antes de escribir: neo4j, 127.0.0.1:7687. Inicialmente había cero
nodos, cero relaciones, ninguna restricción y dos índices LOOKUP. Se conservaron
esos índices. Se crearon exclusivamente las ocho restricciones únicas sobre id y
el índice compuesto Evaluacion(anio_ingreso, aprobado). Los ocho índices de respaldo
de las restricciones son creados automáticamente por Neo4j; no son índices adicionales
solicitados por el cargador. Todos los índices quedaron ONLINE.

Se seleccionaron las primeras 500 evaluaciones por _id ascendente de MongoDB y se
materializó exactamente el mismo lote para ambas llamadas al cargador. No se invocó
la carga completa. Manifestación de ids y reporte: data/reports/neo4j/prueba-500/resultado.json.
Huella del lote: ee82022fae56500eacb1f58bc9de78067e6fd073613e1f03283e6174dd06a7c1.

| Nodo | Primera carga | Repetición |
| --- | ---: | ---: |
| Evaluacion | 500 | 500 |
| AspiranteCohorte | 499 | 499 |
| Cohorte | 10 | 10 |
| Materia | 3 | 3 |
| CarreraObservada | 15 | 15 |
| LocalidadEducativa | 94 | 94 |
| Departamento | 21 | 21 |
| TipoInstitucion | 4 | 4 |
| Total | 1146 | 1146 |

| Relación | Primera carga | Repetición |
| --- | ---: | ---: |
| TIENE_REGISTRO | 500 | 500 |
| EN_COHORTE | 500 | 500 |
| DE_MATERIA | 500 | 500 |
| ASPIRA_A | 440 | 440 |
| PROCEDENCIA_EDUCATIVA | 490 | 490 |
| EN_DEPARTAMENTO | 94 | 94 |
| TIPO_INSTITUCION | 490 | 490 |
| Total | 3014 | 3014 |

Se compararon todas las propiedades de los 1146 nodos contra la proyección esperada
en ambas ejecuciones. Cero claves duplicadas por etiqueta y cero relaciones repetidas
por extremos/tipo. Dos evaluaciones pertenecen al mismo aspirante de cohorte: de ahí
499 aspirantes para 500 evaluaciones. Carreras nulas y procedencias ausentes no
producen relaciones ficticias.

Las seis consultas se ejecutaron en transacciones de lectura sin actualizaciones:
01_aprobacion devolvió 21 filas; 02_carreras, 10; 03_visualizacion, 10;
04_aspirante, 1; 05_ambas_materias, 0; 06_procedencia, 19. Parámetros de año 2021,
materia MATEMATICA y una carrera/cohorte reales del lote (detalle en el reporte).
Cero filas en ambas materias es un resultado válido de esta muestra parcial y
no describe todos los datos de admisión. No hubo errores en la prueba.

Verificación manual de lectura:

```cypher
MATCH (n:USACAdmision) RETURN count(n) AS nodos;
MATCH (:USACAdmision)-[r]->(:USACAdmision) RETURN type(r), count(r);
MATCH (e:Evaluacion:USACAdmision) RETURN count(e) AS evaluaciones;
SHOW CONSTRAINTS;
SHOW INDEXES;
```

El checkpoint del CLI completo no se creó durante la prueba de 500.
Posteriormente, las dos cargas completas autorizadas sí generaron sus checkpoints
y reutilizaron esos datos. No se borraron ni reemplazaron datos.


## Cierre validado: carga completa

La fuente fue exclusivamente `usac_admisiones.evaluaciones`; el destino, `neo4j`.
Se conservaron las 500 evaluaciones iniciales y se ejecutaron dos pasadas completas
de 208453 evaluaciones, en 417 lotes por pasada (416 de 500 y uno de 453).

| Verificación | Primera pasada | Segunda pasada |
| --- | ---: | ---: |
| Evaluaciones procesadas | 208453 | 208453 |
| Nodos de evaluación almacenados | 208453 | 208453 |
| Total de nodos | 265293 | 265293 |
| Total de relaciones | 1222881 | 1222881 |
| Duplicados de nodos / relaciones | 0 / 0 | 0 / 0 |
| Tiempo de carga, segundos | 264.157 | 185.044 |

En ambas pasadas se compararon las propiedades de los 265293 nodos y el conjunto
completo de 1222881 relaciones contra la proyección. Los conteos por tipo coinciden
con las tablas de la simulación. La huella de propiedades fue idéntica en ambas.
Se verificaron las ocho restricciones y todos los índices ONLINE, conservando los
dos LOOKUP previos. No hubo errores. El tiempo total, incluyendo prevalidación,
ambas cargas, comprobaciones de integridad y consultas, fue 645.182 segundos.

Las seis consultas se ejecutaron sin escrituras, con año 2024 (también desde/hasta
2024 para la primera), materia MATEMATICA y carrera/cohorte reales de la fuente:

| Archivo | Filas | Tiempo observado, segundos |
| --- | ---: | ---: |
| `01_aprobacion.cypher` | 2 | 0.144 |
| `02_carreras.cypher` | 9 | 0.207 |
| `03_visualizacion.cypher` | 100 | 0.147 |
| `04_aspirante.cypher` | 7 | 0.071 |
| `05_ambas_materias.cypher` | 100 | 0.296 |
| `06_procedencia.cypher` | 58 | 0.272 |

Estos tiempos son observaciones locales, no garantías de rendimiento. Las consultas
03 y 05 están limitadas a 100 resultados; las demás utilizan filtros o agregaciones.
Los resultados del lote pequeño no deben confundirse con los del conjunto completo.

Los reportes completos están en `data/reports/neo4j/carga-completa/resultado.json`,
con checkpoints separados en `pasada-1/checkpoint.json` y `pasada-2/checkpoint.json`.
Esos archivos locales, los CSV y los reportes grandes están excluidos de Git.
Las cargas se supervisaron con un script temporal que invocó `execute` del mismo
cargador del repositorio y comprobó el grafo completo; ese supervisor no se versiona.
El CLI permite reproducir la carga y guardar checkpoints, pero el reporte detallado
de tiempos e integridad de esta ejecución pertenece al supervisor local.

Una revisión posterior confirmó que no existían procesos de carga ni otras
transacciones activas: ambas pasadas habían finalizado, no estaban interrumpidas.
Ambos checkpoints corresponden al máximo _id de MongoDB; 208453 documentos están
confirmados y quedan cero pendientes. No es necesario reanudar.

Si una ejecución futura se interrumpe, comprobar primero procesos, conteos y la
identidad del checkpoint. El comando de reanudación de la segunda pasada sería:

```bash
PYTHONPATH=backend .venv/bin/python -m app.graph --execute --resume --batch-size 500 --output-dir data/reports/neo4j/carga-completa/pasada-2
```

No ejecutar otra carga si existe una activa. La fuente debe permanecer sin cambios.
La repetición completa usa --execute sin --resume: MERGE conserva los nodos y
relaciones existentes. No se hicieron commits, merges ni push durante esta etapa.
