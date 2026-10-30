# Análisis de Pruebas Específicas de Admisión USAC

Plataforma web para explorar y analizar los resultados históricos de las pruebas específicas de admisión de la Facultad de Ingeniería de la **Universidad de San Carlos de Guatemala (USAC)**. Integra estadísticas, filtros interactivos y exploración de relaciones para facilitar la interpretación de los datos publicados.

## Características

- **Resumen general:** indicadores de evaluaciones, resultados aprobados y no aprobados, y porcentaje de aprobación.
- **Análisis estadístico:** tendencias por año y materia, resultados por carrera y procedencia educativa.
- **Consulta de evaluaciones:** exploración de registros con filtros y paginación.
- **Explorador de grafos:** visualización interactiva de relaciones en Neo4j, con filtros, selección de nodos e inspección de propiedades.
- **Consultas NoSQL:** catálogo de **30 consultas MongoDB** y **6 consultas Cypher** para explorar diferentes aspectos de los datos.

## Tecnologías

| Componente | Tecnología |
| --- | --- |
| Interfaz web | React y Vite |
| API | Python y FastAPI |
| Base de datos documental | MongoDB |
| Base de datos de grafos | Neo4j |
| Procesamiento de datos | ETL en Python |
| Entorno de bases de datos | Docker Compose |
| Pruebas | Pruebas automatizadas de backend, frontend y navegador |

## Arquitectura general

```text
Archivos CSV de admisión
          |
          v
     Proceso ETL
       /     \
      v       v
  MongoDB    Neo4j
       \      /
        v    v
      API FastAPI
           |
           v
      React + Vite
```

MongoDB almacena los registros y permite realizar análisis documentales. Neo4j representa las relaciones entre evaluaciones y su contexto. La API proporciona los datos a la aplicación web.

## Requisitos

- Python 3.12
- Node.js 22.12 o superior, dentro de la versión 22
- npm 10
- Docker con Compose v2

Los siguientes comandos se ejecutan desde la raíz del repositorio, en Linux.

## Instalación

### 1. Obtener el proyecto

```bash
git clone https://github.com/MelanniTzul/proyecto-nosql-usac.git
cd proyecto-nosql-usac
```

### 2. Instalar dependencias

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements-dev.txt
npm ci --prefix frontend
```

### 3. Configurar las variables de entorno

```bash
cp .env.example .env
chmod 600 .env
```

Editar `.env` y establecer las credenciales correspondientes de MongoDB y Neo4j. **No publicar este archivo ni incluir contraseñas en el código.**

### 4. Iniciar las bases de datos

En una instalación nueva:

```bash
docker compose up -d --wait --wait-timeout 240
```

Si los contenedores ya existen y están detenidos, utilizar:

```bash
docker compose start
```

### 5. Preparar los datos (solo en una instalación nueva)

Obtener los archivos CSV de la [fuente oficial de datos abiertos de Ingeniería USAC](https://datosabiertos.ingenieria.usac.edu.gt/en/dataset/pruebas-especificas) y colocarlos en `data/raw`, con los nombres `pruebas_especificas_2015.csv` a `pruebas_especificas_2024.csv`.

Primero analizar los archivos y realizar una simulación de carga:

```bash
PYTHONPATH=backend .venv/bin/python -m app.etl analyze
PYTHONPATH=backend .venv/bin/python -m app.etl load --dry-run --batch-size 1000
```

Después de verificar los resultados, inicializar las bases de datos:

```bash
PYTHONPATH=backend .venv/bin/python -m app.etl load --execute --batch-size 1000
PYTHONPATH=backend .venv/bin/python -m app.graph --dry-run
PYTHONPATH=backend .venv/bin/python -m app.graph --execute --batch-size 500
```

**Importante:** estos comandos de carga no son necesarios si las bases ya contienen los datos. No eliminar volúmenes ni volver a inicializar una instalación que ya funciona.

## Ejecución

Iniciar el backend en una terminal:

```bash
.venv/bin/python -m uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

Iniciar el frontend en otra terminal:

```bash
npm run dev --prefix frontend
```

| Servicio | Dirección |
| --- | --- |
| Aplicación web | http://127.0.0.1:5173 |
| Documentación interactiva de la API | http://127.0.0.1:8000/docs |
| Estado de las bases de datos | http://127.0.0.1:8000/api/health/databases |
| Neo4j Browser | http://127.0.0.1:7474 |

## Consultas NoSQL

El proyecto incluye un catálogo de **30 consultas MongoDB** y **6 consultas Cypher** de Neo4j. Estas consultas permiten analizar aprobaciones, tendencias, materias, carreras, procedencia educativa, calidad de los registros y relaciones entre entidades.

Las consultas están disponibles desde la sección **Consultas NoSQL** de la aplicación.

Para listar o ejecutar las consultas MongoDB desde la terminal:

```bash
PYTHONPATH=backend .venv/bin/python -m app.queries.mongodb --list
PYTHONPATH=backend .venv/bin/python -m app.queries.mongodb --all
```

Consultar el [catálogo documentado de MongoDB](docs/consultas-mongodb.md), el [catálogo de consultas](consultas/mongodb/catalogo.json) y la [documentación de Neo4j](docs/etapa-4.md) para conocer su objetivo, implementación e interpretación.

## Pruebas

Con las dependencias instaladas y las bases disponibles, ejecutar los siguientes comandos **secuencialmente**:

```bash
USAC_RUN_DB_TESTS=1 PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -v
npm test --prefix frontend
npm run build --prefix frontend
npm run test:e2e --prefix frontend
```

Las pruebas de navegador requieren Google Chrome. Para más información sobre el entorno y los procedimientos de validación, consultar el manual técnico.

## Documentación

- [Manual técnico](docs/manual-tecnico.md): arquitectura, instalación, modelos, ETL, pruebas y mantenimiento.
- [Manual de usuario](docs/manual-usuario.md): navegación, filtros, estadísticas, evaluaciones y explorador de grafos.
- [Consultas MongoDB](docs/consultas-mongodb.md): catálogo de 30 consultas con ejemplos y resultados.
- [Consultas Neo4j](docs/etapa-4.md): modelo de grafos y seis consultas Cypher.
- [Explorador de consultas](docs/explorador-consultas.md): funcionamiento de la sección Consultas NoSQL.
- [Proceso ETL](docs/etapa-3.md): preparación, validación y carga de datos.

## Alcance de los datos

El conjunto de datos validado comprende **208,453 registros de evaluaciones** correspondientes al período **2015–2024**. Cada registro representa una evaluación publicada, no necesariamente una persona distinta. La procedencia geográfica se refiere a la institución educativa registrada y no debe interpretarse como residencia del aspirante.

El análisis conserva los valores y las ausencias presentes en los archivos originales. Los indicadores deben interpretarse dentro del alcance de la información disponible.

## Fuente de datos

[Portal de Datos Abiertos de la Facultad de Ingeniería, USAC](https://datosabiertos.ingenieria.usac.edu.gt/en/dataset/pruebas-especificas).

---

**Proyecto académico — Ingeniería en Ciencias y Sistemas, Universidad de San Carlos de Guatemala.**