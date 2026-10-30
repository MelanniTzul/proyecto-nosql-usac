# Análisis de Pruebas Específicas de Admisión USAC

Proyecto individual de Bases de Datos NoSQL, Ingeniería en Ciencias y Sistemas,
Universidad de San Carlos de Guatemala. React/Vite consume una API FastAPI de
lectura: estadísticas MongoDB y exploración de relaciones Neo4j.

La instalación validada contiene **208,453 evaluaciones**, **265,293 nodos** y
**1,222,881 relaciones**. Las cargas se repitieron sin duplicados. La aplicación
consulta datos reales; no utiliza estadísticas simuladas si falla una conexión.
Incluye un catálogo ejecutable de 30 consultas MongoDB que reutiliza la API existente.

## Documentación de entrega

- [Manual técnico](docs/manual-tecnico.md): arquitectura, instalación, variables,
  Docker, ETL, modelos, inventario de consultas, recuperación y pruebas.
- [Manual de usuario](docs/manual-usuario.md): navegación, pantallas y Consultas NoSQL,
  filtros, paginación, grafo y resolución de problemas.
- [ETL](docs/etapa-3.md), [Neo4j y seis consultas Cypher](docs/etapa-4.md),
  [API y Swagger](docs/etapa-5.md), [frontend y pruebas de navegador](docs/etapa-6.md).
- [Estructura inicial](docs/etapa-1.md) y [conexiones](docs/etapa-2.md) conservan
  el historial técnico de las etapas anteriores.

## 1. Requisitos y código completo

Python 3.12 con venv; Node.js >=22.12.0 y <23; npm 10; Docker con Compose v2.
Google Chrome solo es necesario para las pruebas automatizadas de navegador.
Ejecutar los comandos desde la raíz del proyecto en Linux.

Usar la carpeta de entrega completa. Si se obtiene de GitHub, la rama publicada
debe contener las etapas 5 y 6 y los manuales: el main histórico no garantiza eso.
**La integración actual está en feature/explorador-consultas y sigue pendiente
de publicación**. El catálogo de consola ya está integrado en develop.
Para obtener todo el contenido actual, después de publicar esta rama:

```bash
git clone --branch feature/explorador-consultas https://github.com/MelanniTzul/proyecto-nosql-usac.git
cd proyecto-nosql-usac
```

Si la rama aún no está publicada, trabajar con la carpeta local revisada y omitir
el clon. No descartar cambios para cambiar de rama. Los siguientes pasos permiten
inicializar una instalación nueva; una instalación ya poblada no necesita recargas.

## 2. Instalar dependencias

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements-dev.txt
npm ci --prefix frontend
.venv/bin/python -m pip check
```

requirements-dev.txt incluye las dependencias de ejecución y pruebas. Las versiones
se fijan en los archivos requirements y package-lock.json. No versionar las carpetas
de dependencias ni el entorno virtual.

## 3. Configurar `.env`

Crear el archivo únicamente si no existe:

```bash
if [ ! -f .env ]; then cp .env.example .env; fi
chmod 600 .env
```

Editar MONGO_ROOT_USERNAME, MONGO_ROOT_PASSWORD y NEO4J_PASSWORD con valores propios
antes de la primera inicialización. Conservar las credenciales si los volúmenes ya
existen: modificar `.env` no cambia automáticamente las contraseñas de las bases.
Neo4j requiere contraseña de al menos ocho caracteres. No publicar este archivo.

Los valores predeterminados usan MongoDB 127.0.0.1:27017, autenticación en admin y
Neo4j 127.0.0.1:7687, base neo4j. La colección de evaluaciones es
usac_admisiones.evaluaciones; admin es autenticación, no el destino de los datos.
Opciones de CORS y timeout en .env.example y el manual técnico. Nunca enviar las
credenciales de las bases a React.

## 4. Iniciar Docker

En una instalación nueva:

```bash
docker compose config --quiet
docker compose up -d --wait --wait-timeout 240
docker compose ps
```

Si los contenedores existentes están detenidos, usar `docker compose start`.
MongoDB 8.0.16 y Neo4j 5.26.12 Community conservan datos en volúmenes del proyecto
usac-nosql. No recrear volúmenes ni cambiar contraseñas para iniciar el frontend.

## 5. Preparar los datos en una instalación vacía

Descargar los CSV desde la [fuente oficial](https://datosabiertos.ingenieria.usac.edu.gt/en/dataset/pruebas-especificas)
y colocarlos en data/raw como pruebas_especificas_2015.csv hasta
pruebas_especificas_2024.csv. Los CSV no están en Git; Docker nuevo no los carga.
Se esperan diez archivos y 208,453 filas en el conjunto validado.

Primero analizar y simular, sin escrituras a bases:

```bash
mkdir -p data/raw
PYTHONPATH=backend .venv/bin/python -m app.etl analyze
PYTHONPATH=backend .venv/bin/python -m app.etl load --dry-run --batch-size 1000
```

Después de revisar los reportes y **solo para inicializar la instalación que se
quiere cargar**, estos comandos escriben de forma aditiva e idempotente:

```bash
PYTHONPATH=backend .venv/bin/python -m app.etl load --execute --batch-size 1000
PYTHONPATH=backend .venv/bin/python -m app.graph --dry-run
PYTHONPATH=backend .venv/bin/python -m app.graph --execute --batch-size 500
```

No ejecutar esas cargas en la instalación ya validada para iniciar la aplicación.
Este cierre documental no las ejecuta. Se preservan originales, advertencias y
repeticiones de fuente. Archivos con contenido modificado requieren revisión antes
de cargarse como otra versión. Reportes y checkpoints locales: data/reports.
Consultar [ETL](docs/etapa-3.md) y [manual técnico](docs/manual-tecnico.md) para reglas
de validación, resultados por año y recuperación tras una interrupción.

## 6. Iniciar backend y frontend

Terminal 1:

```bash
.venv/bin/python -m uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

Terminal 2:

```bash
npm run dev --prefix frontend
```

| Servicio | Dirección |
| --- | --- |
| Aplicación React | http://127.0.0.1:5173 |
| Swagger | http://127.0.0.1:8000/docs |
| OpenAPI JSON | http://127.0.0.1:8000/openapi.json |
| Salud de la API | http://127.0.0.1:8000/api/health |
| Estado de bases | http://127.0.0.1:8000/api/health/databases |
| Neo4j Browser | http://127.0.0.1:7474 |

El frontend consulta /api mediante el proxy de Vite. El encabezado muestra
**Bases disponibles** si ambas comprobaciones tienen éxito; su icono permite
reintentar. El cliente tiene timeout HTTP de 20 segundos. Las consultas mantienen
sus propios límites de servidor. /api/health solo verifica el proceso; el endpoint
/health/databases comprueba MongoDB y Neo4j sin escribir.

Si los puertos están ocupados, no detener procesos desconocidos. Usar backend 8001:

```bash
.venv/bin/python -m uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8001
```

Y frontend 5174 en otra terminal:

```bash
API_PROXY_TARGET=http://127.0.0.1:8001 FRONTEND_PORT=5174 npm run dev --prefix frontend
```

Abrir http://127.0.0.1:5174. frontend/.env.example documenta esas variables.

## 7. Verificación y pruebas secuenciales

Con ambas bases disponibles, ejecutar **una orden después de otra**, no en paralelo:

```bash
USAC_RUN_DB_TESTS=1 PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -v
npm test --prefix frontend
npm run build --prefix frontend
npm run test:e2e --prefix frontend
git diff --check
```

Se verificaron 54 pruebas backend, 17 frontend y 10 de navegador, incluyendo
la ejecución y visualización de las 30 consultas MongoDB y las 6 Cypher. La integración
real es de lectura; las pruebas que simulan cargas usan dobles en memoria.
Playwright requiere Google Chrome, crea servidores propios en 8010 y 5180 y los
cierra al finalizar; esos puertos deben estar libres. No requiere apagar los
servidores de desarrollo en 8000/5173. Las consultas de control conservaron los
conteos de las bases. Evitar ejecutar simultáneamente pruebas de credenciales y
pruebas de navegador; una auditoría concurrente tuvo errores 503 y su repetición
secuencial pasó sin cambios de código.

Para comprobar la API manualmente:

```bash
curl --fail http://127.0.0.1:8000/api/health
curl --fail http://127.0.0.1:8000/api/health/databases
curl --fail http://127.0.0.1:8000/api/estadisticas
```

Para revisar el build local: `npm run preview --prefix frontend`, puerto 4173,
manteniendo FastAPI activo. Preview no sustituye un servidor de producción.
Un despliegue requiere fallback de rutas React a index.html y proxy /api a FastAPI.

## 8. Catálogo de 30 consultas MongoDB y seis Cypher

El catálogo [consultas/mongodb/catalogo.json](consultas/mongodb/catalogo.json)
contiene **30 consultas MongoDB diferentes**, documentadas con objetivo, código
Python/PyMongo ejecutable, explicación y resultados reales en
[docs/consultas-mongodb.md](docs/consultas-mongodb.md).

Se reutilizan directamente las siete operaciones válidas de
backend/app/services/mongo_analytics.py y se añaden 23 análisis complementarios.
No se agregan 30 endpoints ni se cuentan cambios de filtros como consultas nuevas.
Las rutas existentes conservan sus contratos. La sección **Consultas NoSQL** en
http://127.0.0.1:5173/consultas permite seleccionar y ejecutar las 30 consultas
MongoDB y las seis Cypher, con tablas y grafos en los casos de caminos. Tres rutas
GET cerradas gestionan catálogo y ejecución por id; no se acepta código arbitrario.
Ver [uso y seguridad del explorador](docs/explorador-consultas.md). El catálogo cubre el requisito
indicado de al menos 20 consultas y amplía el análisis a sexo, carreras, procedencia,
completitud, advertencias, duplicados de fuente y aspirantes dentro de su cohorte.

```bash
PYTHONPATH=backend .venv/bin/python -m app.queries.mongodb --list
PYTHONPATH=backend .venv/bin/python -m app.queries.mongodb --all
PYTHONPATH=backend .venv/bin/python -m app.queries.mongodb --id 24 --output data/reports/consulta-24.json
```

Estas órdenes solo leen MongoDB. --list no conecta a las bases. --all ejecuta las
consultas secuencialmente y verifica invariantes; el reporte completo se guarda
en data/reports/consultas-mongodb.json, excluido de Git. Se usa un presupuesto
cliente de consola de 60 segundos por consulta, sin cambiar el timeout de la API.
La consulta 24 puede usar temporales internos de agregación, sin escribir resultados
en colecciones ni modificar originales.

Se conservan sin cambios las **seis consultas Cypher** en consultas/neo4j,
documentadas en [etapa 4](docs/etapa-4.md) y en el catálogo MongoDB. No se ejecutan
cargas Neo4j desde estas consultas. La colección materializada resumen_carrera
mencionada en el plan inicial sigue sin implementarse; es distinta del catálogo
analítico de lectura y no se crea como efecto de la verificación.

Limitaciones de interpretación: registros no equivalen a personas globales;
aspirante de cohorte significa año + correlativo. Se conservan carreras/municipios
recortados y datos ausentes. La procedencia es educativa, no residencia. Aprobar
ambas materias no demuestra admisión definitiva.

## 9. Persistencia y Git

Detener solo procesos propios con Ctrl+C. `docker compose stop` conserva datos.
No ejecutar `docker compose down -v` ni borrar bases, colecciones o registros.
.gitignore excluye .env, frontend/.env.local, data/raw, data/reports, .venv,
node_modules, dist y cachés. Las plantillas .env.example y lockfiles sí se versionan.
La integración actual se desarrolla en feature/explorador-consultas y queda
pendiente de autorización para commit, merge y push. No hay publicaciones automáticas.
