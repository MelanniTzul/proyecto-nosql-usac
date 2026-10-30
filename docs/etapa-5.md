# Etapa 5: API FastAPI para React

Rama `feature/fastapi-endpoints`. Los endpoints realizan únicamente lecturas.
Reutilizan DatabaseConnections, creadas en lifespan y cerradas al finalizar el
proceso. No ejecutan ETL, crean índices ni modifican documentos, nodos o relaciones.
No se necesitan dependencias adicionales.

## Iniciar y abrir Swagger

Con las bases existentes activas, desde la raíz:

```bash
.venv/bin/python -m uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

Abrir http://127.0.0.1:8000/docs. Usar **Try it out**, completar parámetros y
**Execute**. Los modelos de respuestas, filtros y errores aparecen en OpenAPI:
http://127.0.0.1:8000/openapi.json. Si el puerto 8000 está ocupado, usar 8001 sin
detener servicios existentes y ajustar API_PROXY_TARGET en Vite. React puede seguir
usando `/api` a través de su proxy; no se cambiaron sus componentes.

Conservar `.env` existente. Las variables opcionales nuevas están en `.env.example`:

```dotenv
API_QUERY_TIMEOUT_SECONDS=10
CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]
```

El timeout admite 1–30 segundos y limita las operaciones de consulta (MongoDB
maxTimeMS, Neo4j timeout de transacción). DB_TIMEOUT_SECONDS conserva los límites de
conexión y socket existentes; no es un límite global para toda la petición HTTP.
Una ruta con varias consultas puede durar más que un timeout individual.

CORS acepta una lista JSON de orígenes HTTP/HTTPS exactos, sin rutas, credenciales,
comodines ni barra final. `localhost` y `127.0.0.1` son orígenes distintos. Se permiten
lecturas GET y preflight OPTIONS, sin cookies ni credenciales del navegador. Cambiar
las variables requiere reiniciar el backend. CORS controla acceso del navegador;
no sustituye autenticación. Los errores de validación de consultas no incluyen los
valores recibidos. No se modificó el `.env` local.

HTTPSettings permite configurar CORS al construir la aplicación, sin crear clientes
de bases. Settings hereda esas opciones y añade las credenciales y la configuración
existentes. `create_app()` permite aislar la aplicación en pruebas; `app` sigue
siendo compatible con el comando Uvicorn anterior.

## Endpoints

| Método y ruta | Fuente | Parámetros |
| --- | --- | --- |
| GET /api/health | Proceso | Ninguno |
| GET /api/health/databases | MongoDB y Neo4j | Ninguno |
| GET /api/estadisticas | MongoDB | anio, materia, aprobado opcionales |
| GET /api/evaluaciones | MongoDB | anio, materia, aprobado, limite, cursor opcionales |
| GET /api/catalogos | MongoDB | Ninguno |
| GET /api/estadisticas/aprobacion | MongoDB | desde=2015, hasta=2024 |
| GET /api/resultados/carreras | MongoDB | anio obligatorio, materia opcional |
| GET /api/procedencia | MongoDB | anio obligatorio |
| GET /api/resultados/ambas-materias | MongoDB | anio obligatorio, limite=50 |
| GET /api/grafo | Neo4j | anio obligatorio; materia, aprobado, carrera_id y limite=25 opcionales |
| GET /api/grafo/aspirantes/{cohorte_id} | Neo4j | cohorte_id obligatorio, limite=25 |

Años: 2015–2024; desde no puede superar hasta. Materias: MATEMATICA, COMPUTACION,
MATEMATICA ITUGS. Aprobación: true/false. Los filtros estructurados rechazan campos
desconocidos. Carrera_id tiene formato `carrera:` seguido de 64 caracteres hexadecimales;
se obtiene de /api/catalogos, sin calcularlo en React. Cohorte_id es año:correlativo.
Un identificador con formato válido pero sin datos no es necesariamente un error:
listas y filtros devuelven lista/grafo vacío; aspirante concreto inexistente devuelve 404.

Todas las estadísticas y catálogos se consultan en usac_admisiones.evaluaciones.
Los endpoints de grafos consultan exclusivamente la base neo4j y la etiqueta
USACAdmision. No hay consultas arbitrarias proporcionadas por el navegador.
Las conexiones son compartidas, pero cada consulta Neo4j usa su propia sesión con
READ_ACCESS. Las rutas síncronas ejecutan los controladores existentes en el grupo
de hilos de FastAPI. Un fallo de Neo4j no impide consultar MongoDB, y viceversa.

La decisión final de esta etapa es usar MongoDB para todas las estadísticas, según
la condición aprobada al implementar. Los agregados equivalen a los análisis de
las consultas Cypher 01, 02, 05 y 06, que permanecen disponibles como consultas
independientes. La visualización reutiliza los recorridos de 03 y 04, adaptados para
filtrar/limitar evaluaciones antes de expandir y admitir carreras ausentes. Los seis
archivos originales en consultas/neo4j permanecen intactos.

## JSON y significado

Los dos endpoints de salud conservan su contrato existente para no romper React.
Los nueve nuevos usan el mismo sobre:

```json
{
  "status": "ok",
  "data": [],
  "meta": {
    "fuente": "mongodb",
    "filtros": {"anio": 2024},
    "limite": 50,
    "siguiente_cursor": null,
    "truncado": false,
    "notas": []
  }
}
```

`data` es un objeto en estadísticas, catálogos y grafos, y una lista en el resto.
Los modelos Pydantic documentan y validan cada respuesta. No se serializan objetos
BSON o del controlador Neo4j directamente. Las evaluaciones usan `id` y omiten los
originales completos y el correlativo separado: conservan cohorte_id y advertencias.
MongoDB sigue preservando los originales sin alteración.

Los conteos representan registros de fuente, incluidas sus repeticiones originales.
No se identifican personas globales. Carreras se agrupan por valor y estado, sin
unir nombres completos y recortados. Estadísticas por carrera incluyen la ausencia
como carrera/id nulos y estado ausente. Procedencia incluye categorías nulas: por
eso puede devolver una fila más que la consulta Cypher 06, que exige relaciones.
La ubicación es educativa, no residencia. Ambas materias significa aprobación
informada en Matemática y Computación dentro de la cohorte, no admisión definitiva.
MATEMATICA ITUGS no se cuenta como MATEMATICA en esa consulta.

La tasa es aprobados/registros * 100, redondeada a dos decimales. Si el denominador
es cero, se devuelve null. No se inventa un porcentaje para una selección vacía.

## Paginación y grafo

Evaluaciones: limite predeterminado 50, máximo 100. Orden ascendente por _id;
el servidor lee limite+1 registros y devuelve siguiente_cursor si hay más.
Repetir la llamada con ese cursor y los mismos filtros anio/materia/aprobado.
El cursor contiene último id y una huella de los filtros; no es un secreto ni un
token de autorización. No se admite saltar a un número de página ni cambiar los
filtros conservando cursor. La API no obtiene un total con cada página para evitar
trabajo adicional. Para totales usar estadísticas. El conjunto debe mantenerse
estable si se quiere recorrer una fotografía exacta; la paginación no crea snapshots.

Ambas materias: hasta 100 resultados, con truncado si hay más; no tiene cursor.
Los catálogos/agregados tienen tamaño acotado por las categorías reales, sin
paginación de documentos. No se aplica un límite a grupos que altere sus totales.

Grafo: primero seleccionar hasta limite+1 evaluaciones con filtros (máximo 100).
Después expandir solo las primeras limite. Topes adicionales: 500 nodos y 800
relaciones. `truncado` indica que hay más evaluaciones o se alcanzó un tope. El grafo
no tiene cursor; cambiar filtros para explorar otra selección. Los nodos y relaciones
se deduplican y ninguna relación devuelta apunta a un nodo ausente.

```json
{
  "nodes": [{"id": "Evaluacion:hash", "tipo": "Evaluacion", "properties": {"id": "hash"}}],
  "edges": [{"id": "relacion:hash", "source": "AspiranteCohorte:cohorte", "target": "Evaluacion:hash", "tipo": "TIENE_REGISTRO"}]
}
```

El ejemplo anterior solo muestra el formato; una respuesta real incluye también el
nodo source. El id de interfaz lleva etiqueta + clave, evitando colisiones entre
tipos. La clave de relación es determinista por origen/tipo/destino, sin depender
de elementId interno de Neo4j. No se realizan recorridos de longitud ilimitada.
Se aprovechan los índices existentes de MongoDB y las restricciones/índice compuesto
de Neo4j. No se crea ningún índice desde las rutas HTTP. Se verificaron planes con
explain de MongoDB y EXPLAIN Cypher, además de filtros y topes con datos reales.

## Errores

```json
{
  "status": "error",
  "error": {
    "code": "INVALID_PARAMETERS",
    "message": "Revisa los parámetros enviados.",
    "details": [{"campo": "query.anio", "mensaje": "Valor inválido o parámetro no permitido."}]
  }
}
```

422: filtros/cursor inválidos; 404: aspirante o ruta inexistente; 405: método no
permitido; 503: base inaccesible; 504: timeout de consulta; 500: fallo interno.
Las respuestas no exponen excepciones, contraseñas ni valores de entrada. Los
preflight CORS los atiende el middleware y conservan su respuesta estándar.

## Probar cada endpoint

Con Uvicorn en el puerto 8000:

```bash
curl --fail http://127.0.0.1:8000/api/health
curl --fail http://127.0.0.1:8000/api/health/databases
curl --fail http://127.0.0.1:8000/api/estadisticas
curl --fail 'http://127.0.0.1:8000/api/evaluaciones?anio=2024&materia=MATEMATICA&aprobado=false&limite=3'
curl --fail http://127.0.0.1:8000/api/catalogos
curl --fail 'http://127.0.0.1:8000/api/estadisticas/aprobacion?desde=2024&hasta=2024'
curl --fail 'http://127.0.0.1:8000/api/resultados/carreras?anio=2024&materia=MATEMATICA'
curl --fail 'http://127.0.0.1:8000/api/procedencia?anio=2024'
curl --fail 'http://127.0.0.1:8000/api/resultados/ambas-materias?anio=2024&limite=3'
curl --fail 'http://127.0.0.1:8000/api/grafo?anio=2024&materia=MATEMATICA&aprobado=false&limite=5'
```

Para probar el endpoint de aspirante, tomar properties.id de un nodo
AspiranteCohorte devuelto por /api/grafo y usarlo como cohorte_id en Swagger.
Este ejemplo automatiza esa selección sin modificar datos:

```bash
python3 - <<'PY'
import json
from urllib.request import urlopen
from urllib.parse import quote
base = 'http://127.0.0.1:8000'
with urlopen(base + '/api/grafo?anio=2024&limite=5') as response:
    graph = json.load(response)
cohort = next(n['properties']['id'] for n in graph['data']['nodes'] if n['tipo'] == 'AspiranteCohorte')
with urlopen(base + '/api/grafo/aspirantes/' + quote(cohort, safe='') + '?limite=3') as response:
    print(json.dumps(json.load(response), ensure_ascii=False, indent=2))
PY
```

En Swagger también se puede continuar /api/evaluaciones copiando siguiente_cursor.
Para probar validación: /api/evaluaciones?limite=101 debe responder 422.

## Pruebas automatizadas

Pruebas HTTP con dobles de conexión, sin acceder a bases:

```bash
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p test_api.py -v
```

Integración real optativa y exclusivamente de lectura:

```bash
USAC_RUN_DB_TESTS=1 PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p test_api_readonly.py -v
```

Suite completa, incluidas las pruebas de salud existentes y ETL/grafo:

```bash
USAC_RUN_DB_TESTS=1 PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -v
```

El módulo test_api_readonly se omite si no se establece USAC_RUN_DB_TESTS=1.
Las pruebas de salud existentes sí requieren las bases reales. Las pruebas nuevas
usan TestClient para HTTP y las conexiones oficiales para integración; no necesitan
ocupar un puerto Uvicorn. En el entorno restringido del agente TestClient bloqueó
el arranque de su bucle asíncrono; fuera del sandbox la suite funcionó, sin cambios
de dependencias. En una terminal local se usan los comandos anteriores normalmente.

Se cubren filtros inválidos, ausencia de consultas ante errores de parámetros,
cursores malformados y asociados a otros filtros, paginación sin solapamiento,
proyección de campos, ausencia de datos, división por cero, errores seguros,
independencia entre bases, CORS, Swagger/OpenAPI, serialización de grafos,
deduplicación y relaciones sin extremos ausentes. La integración comprueba todos
los endpoints, conteos de grupos, planes de consulta y límite máximo del grafo.
Los conteos globales antes/después se guardan en el reporte local
`data/reports/etapa-5/verificacion-api.json`, excluido de Git.

Los conteos iguales no prueban por sí solos que ningún campo cambiara; las nuevas
consultas se revisaron también para confirmar que solo contienen find/aggregate,
MATCH/RETURN y EXPLAIN, sin escrituras ni creación de índices. Las pruebas ETL y
grafo que simulan escrituras siguen usando dobles en memoria.


## Resultados verificados

Suite completa: **38 pruebas correctas** (10 API aisladas, 5 API con bases reales,
6 salud/conexiones, 9 ETL y 8 grafo). Swagger /docs y el esquema /openapi.json
respondieron 200 mediante TestClient; OpenAPI documenta 11 rutas GET. No se inició
ni detuvo ningún servidor de desarrollo existente para estas pruebas.

Todas las solicitudes válidas de integración respondieron 200. Las pruebas también
verificaron 404 para aspirante inexistente y 422 para filtros/cursor inválidos.

| Endpoint / selección | Resultado observado |
| --- | --- |
| /api/health | ok, contrato anterior conservado |
| /api/health/databases | Ambas bases ok |
| /api/estadisticas | 208453 registros, 29877 aprobados, 178576 no aprobados, 14.33% |
| /api/evaluaciones, 2024, MATEMATICA, false, limite=3 | Dos páginas de tres registros sin ids repetidos |
| /api/catalogos | Diez años, tres materias y carreras con estado explícito |
| /api/estadisticas/aprobacion, año 2024 | Dos grupos; total 13863 registros |
| /api/resultados/carreras, año 2024 | Nueve grupos; total 13863 registros |
| /api/procedencia, año 2024 | 59 grupos, incluidos ausentes; total 13863 registros |
| /api/resultados/ambas-materias, año 2024, limite=3 | Tres resultados |
| /api/grafo, año 2024, filtros, limite=5 | 20 nodos, 33 relaciones, truncado=true |
| /api/grafo/aspirantes, cohorte real, limite=3 | 11 nodos, 19 relaciones, truncado=true |
| /api/grafo, año 2024, limite=100 | 256 nodos, 620 relaciones, dentro de topes |

Los conteos antes y después de las pruebas reales fueron idénticos:
208453 documentos MongoDB, 265293 nodos y 1222881 relaciones Neo4j.
Se detectan 56147 registros con advertencias, conservadas en las respuestas.
No se ejecutaron cargas ni cambios de esquema; no hay commits, merges o push.
