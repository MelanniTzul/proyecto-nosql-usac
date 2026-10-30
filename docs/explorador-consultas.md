# Consultas NoSQL desde React

Rama `feature/explorador-consultas`. Se integran **30/30 consultas MongoDB y 6/6
consultas Cypher**. Ninguna queda solo documentada. No se reconstruyeron ni borraron
consultas; las cuatro pantallas anteriores y sus endpoints permanecen disponibles.

## Uso

Iniciar backend y frontend según [README](../README.md), abrir
http://127.0.0.1:5173/consultas o elegir **Consultas NoSQL** en la navegación.

1. Elegir la pestaña MongoDB o Neo4j.
2. Seleccionar el número y nombre de la consulta en Consulta del catálogo.
3. Leer su objetivo, explicación y alcance.
4. En MongoDB, los argumentos son los predefinidos del catálogo (se muestran, no se
   editan). En Neo4j, completar solamente los parámetros requeridos.
5. Pulsar Ejecutar consulta. No se ejecutan análisis por cambiar el selector.
6. Consultar la tabla y, para Cypher 03/04, el grafo y su inspector.

Al seleccionar otra consulta se oculta la salida anterior y se cancela la espera
del navegador. Esto no garantiza cancelar un agregado que ya esté en ejecución en
el servidor. Evitar lanzar consultas pesadas simultáneamente. Reintentar repite la
selección actual. Un resultado vacío sigue siendo una ejecución correcta y se
identifica como tal. No se presentan resultados simulados en caso de error.

La consulta MongoDB 24 compara filas originales y puede tardar más que las consultas
habituales. Tiene hasta 60 segundos de presupuesto de servidor/cliente MongoDB; el
navegador espera hasta 70 segundos solo en esta pantalla. Las pantallas anteriores
conservan su timeout de 20 segundos.

## MongoDB: las treinta consultas

Todas las entradas de [consultas-mongodb.md](consultas-mongodb.md) están en el
selector, con sus mismos ids, definiciones y argumentos. No se agrega un endpoint
por consulta: una ruta cerrada resuelve los ids 1–30. Se reutilizan directamente
las siete funciones existentes y los 23 análisis complementarios. No se cambió el
archivo fuente [catalogo.json](../consultas/mongodb/catalogo.json).

| IDs | Análisis disponibles en React |
| --- | --- |
| 01–05 | Evaluaciones, conteo, resumen, volumen anual y aprobación año/materia |
| 06–08 | Sexo, año/sexo y materia/sexo |
| 09–11 | Carreras, año/carrera y materia/carrera |
| 12–16 | Departamento, municipio/precisión, tipo, departamento/tipo y sexo/tipo |
| 17–20 | Convocatorias, mes de asignación, nacimiento y edad aproximada |
| 21–24 | Completitud, advertencias, textos recortados y repeticiones exactas |
| 25–29 | Cohortes individuales, histograma, ambas materias, múltiples carreras y coexistencia de resultados |
| 30 | Catálogos reales completos |

Las respuestas escalares, objetos, listas y objetos anidados se muestran como tablas.
Los campos anidados de cada fila se aplanan para presentación, sin escribir cambios
en la colección. El resultado incluye id, título, filas de salida y tiempo observado.
La fila de resumen global y los catálogos son objetos; no se confunde su número de
filas de salida con el total de evaluaciones.

Los límites originales de 01 (10 registros con cursor) y 27 (100 aspirantes con
truncado) se conservan; esta pantalla no añade navegación al cursor del catálogo.
La tabla completa de Evaluaciones mantiene su paginación habitual. La consulta 09
del explorador sí muestra el agregado global del catálogo, mientras que Estadísticas
mantiene su análisis por año. Cada lista serializada admite hasta 500 filas, sin
alterar los denominadores ni los pipelines. Si se limita, se muestra un aviso.

## Neo4j: las seis consultas originales

Se ejecuta el contenido de los seis archivos existentes en consultas/neo4j, sin
sustituirlos por consultas MongoDB ni por una imagen de resultados anteriores.

| ID | Archivo | Parámetros | Presentación |
| --- | --- | --- | --- |
| 01 | 01_aprobacion.cypher | desde, hasta | Tabla |
| 02 | 02_carreras.cypher | anio, materia | Tabla |
| 03 | 03_visualizacion.cypher | anio, materia, carrera_id, aprobado | Tabla y grafo |
| 04 | 04_aspirante.cypher | cohorte_id | Tabla y grafo |
| 05 | 05_ambas_materias.cypher | anio | Tabla |
| 06 | 06_procedencia.cypher | anio | Tabla |

Los selectores de años, materias y carreras reutilizan /api/catalogos. Para 03,
la selección inicial de carrera se obtiene de /api/resultados/carreras con el año
y materia elegidos: usa una categoría realmente observada, sin unir nombres completos
y recortados. Se puede cambiar por otra carrera del catálogo y obtener una salida vacía.
Para 04,
pegar un año:correlativo conocido o pulsar **Seleccionar un identificador real de
2024**: se obtiene de /api/evaluaciones?anio=2024&limite=1, sin inventar una persona.
Los identificadores se agrupan por cohorte y no se enlazan automáticamente entre años.

Las consultas 03 y 05 conservan LIMIT 100. Un aviso señala que se alcanzó ese límite;
no afirma conocer cuántas filas adicionales hay. En 03/04 se reutiliza el canvas,
la leyenda, el inspector y la selección accesible del explorador. Consultar esta
cohorte ejecuta la consulta 04 con el id del nodo real seleccionado. Los grafos se
acotan a 500 nodos y 800 relaciones; ninguna relación devuelta carece de extremos.
Los tiempos son observaciones locales y no promesas de rendimiento.

## API y seguridad

| Ruta GET | Función |
| --- | --- |
| /api/consultas | Descripciones de los 30 ids MongoDB y 6 Neo4j, sin consultar bases |
| /api/consultas/mongodb/{consulta_id} | Id 1–30 y argumentos fijos del catálogo |
| /api/consultas/neo4j/{consulta_id} | Id 1–6 y parámetros específicos de ese archivo |

Las tres rutas aparecen en Swagger /docs; OpenAPI tiene ahora 14 rutas GET.
Las respuestas usan status/data/meta. El catálogo tiene fuente catalogo; las
respuestas ejecutadas indican mongodb o neo4j. Los errores conservan el contrato
seguro existente. Id inválido, campos extra, parámetros faltantes o formatos
incorrectos se rechazan antes de consultar la base.

El navegador no envía pipelines, nombres de archivos, texto Cypher, instrucciones
SQL ni operaciones de escritura. No hay editor de consultas arbitrarias. POST no
está permitido. MongoDB utiliza el catálogo validado existente; Neo4j usa una tabla
fija id→archivo y parámetros separados del texto. La lectura de cada archivo también
rechaza cláusulas de escritura o CALL. Las sesiones Neo4j usan READ_ACCESS y timeout
de transacción de 30 segundos. No se crean conexiones por consulta: se reutilizan
los clientes de lifespan.

No se agregan índices ni colecciones. La agregación 24 conserva allowDiskUse para
sus temporales internos, sin persistir resultados ni modificar los documentos.
La colección resumen_carrera no se materializa como parte de esta integración.

## Ejecución y pruebas

El arranque no cambia:

```bash
.venv/bin/python -m uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
npm run dev --prefix frontend
```

Ejecutar cada comando en su terminal. Las pruebas se ejecutan secuencialmente:

```bash
USAC_RUN_DB_TESTS=1 PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -v
npm test --prefix frontend
npm run build --prefix frontend
npm run test:e2e --prefix frontend
git diff --check
```

Los casos nuevos verifican la lista completa, que cada id ejecuta su definición,
rechazo de código arbitrario y parámetros incorrectos, conservación de false,
listas vacías, serialización acotada y ausencia de enlaces sin extremos. Una prueba
HTTP recorre las 36 consultas con bases reales y compara conteos antes/después.
En Chrome hay recorridos que seleccionan, ejecutan y visualizan todos los 30 ids
MongoDB y los 6 Cypher; los dos casos de caminos comprueban canvas visible.
Las pruebas unitarias usan fixtures solo dentro de tests, no como resultados reales.

El reporte HTTP local está en data/reports/explorador-consultas/api.json. Las trazas
Playwright quedan bajo data/reports/etapa-6/playwright, fuera de Git. No se realizan
cargas, modificaciones de datos, commits, merges o push durante esta etapa.

### Resultado de la verificación

La ejecución secuencial terminó correctamente: 54 pruebas backend, 17 frontend y
10 pruebas Chrome; compilación Python y Vite, pip check, configuración Compose y
git diff --check con código 0. Los dos recorridos nuevos ejecutaron cada id desde
React: 30/30 MongoDB con tabla y 6/6 Cypher con tabla, además del canvas en 03/04.
Las 36 ejecuciones HTTP reales respondieron 200. Los conteos antes y después fueron
iguales: 208453 documentos MongoDB, 265293 nodos y 1222881 relaciones Neo4j.
La revisión de los 96 archivos versionados o candidatos no encontró archivos de
datos, reportes generados ni credenciales locales incluidos. Las consultas fuente
MongoDB y los seis archivos Cypher permanecen sin cambios.
