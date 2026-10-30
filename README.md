# Análisis de Pruebas Específicas de Admisión USAC

Proyecto individual de Bases de Datos NoSQL, Ingeniería en Ciencias y Sistemas,
Universidad de San Carlos de Guatemala.

## Estado: segunda etapa

React consulta el endpoint real de FastAPI y muestra conexión, espera, error y
reintento. MongoDB y Neo4j se ejecutan en Docker con autenticación y persistencia.
FastAPI comprueba ambas bases con sus controladores oficiales. El ETL, las consultas,
el dashboard y el explorador de grafos están pendientes; no hay resultados simulados.

La configuración y las pruebas de conexión se explican en [la etapa 2](docs/etapa-2.md).

Los CSV de la [fuente oficial](https://datosabiertos.ingenieria.usac.edu.gt/en/dataset/pruebas-especificas)
deben inspeccionarse antes de implementar transformaciones o fijar los modelos.

## Requisitos e instalación

Python 3.12 con venv, Node.js 22.12 o superior dentro de la rama 22, npm 10 y Docker
con Compose. Las dependencias están fijadas en `backend/requirements.txt` y
`frontend/package-lock.json`.

Desde la raíz del repositorio:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
npm ci --prefix frontend
```

Para una instalación nueva, copiar `.env.example` a `.env` y editar sus contraseñas.
Si `.env` ya existe, conservarlo. Los valores de ejemplo no son secretos reales.

```bash
cp .env.example .env
chmod 600 .env
```

Utilizar contraseñas largas, preferiblemente alfanuméricas; Neo4j requiere al menos
ocho caracteres. Nunca subir `.env` a Git. Cambiarlo después de inicializar los
volúmenes no cambia automáticamente las credenciales almacenadas en las bases.

## Ejecución

Iniciar las bases:

```bash
docker compose config --quiet
docker compose up -d --wait --wait-timeout 240
docker compose ps
```

En otra terminal, desde la raíz, iniciar FastAPI:

```bash
.venv/bin/python -m uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

En otra terminal, desde la raíz, iniciar React:

```bash
npm run dev --prefix frontend
```

| Servicio | Dirección |
| --- | --- |
| Aplicación | http://127.0.0.1:5173 |
| API y OpenAPI | http://127.0.0.1:8000/docs |
| Estado API | http://127.0.0.1:8000/api/health |
| Neo4j Browser | http://127.0.0.1:7474 |

Neo4j utiliza el usuario `neo4j` y la contraseña de `.env`. Los puertos de las
bases se publican solo en la interfaz local. React y FastAPI se ejecutan fuera de
Docker para facilitar la recarga y el aprendizaje.

## Puertos alternativos y permisos

Inspeccionar puertos antes de iniciar otra instancia:

```bash
ss -ltnp '( sport = :8000 or sport = :5173 or sport = :8001 or sport = :5174 )'
```

Si el puerto está ocupado, identificar el proceso y no detenerlo sin autorización.
Una alternativa, en terminales separadas, es:

```bash
.venv/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8001
```

```bash
API_PROXY_TARGET=http://127.0.0.1:8001 npm run dev --prefix frontend -- --port 5174
```

También se puede copiar `frontend/.env.example` a `frontend/.env.local` y configurar
`API_PROXY_TARGET` y `FRONTEND_PORT`; reiniciar Vite tras cambiarlos. Estas variables
no se exponen a React. `strictPort` evita que Vite cambie silenciosamente de puerto.

`EPERM: operation not permitted` al escuchar un puerto puede proceder del entorno
restringido del agente. En ese caso se necesita autorizar la ejecución del servidor
fuera de ese entorno; no se corrige cambiando permisos de archivos ni ejecutando
la aplicación con sudo. `Address already in use` indica un conflicto de puerto.

## Verificación

Con ambos servidores activos, para los puertos predeterminados:

```bash
curl --fail http://127.0.0.1:8000/api/health
curl --fail http://127.0.0.1:5173/api/health
curl --fail http://127.0.0.1:8000/api/health/databases
npm run build --prefix frontend
.venv/bin/python -m pip check
docker compose ps
```

Las peticiones a `/api/health` deben devolver:

```json
{"status":"ok","service":"usac-admisiones-api"}
```

La segunda pasa por el proxy de Vite. En el navegador debe aparecer **API disponible**.
El botón repite la petición. La espera tiene un límite de ocho segundos. El resultado
del endpoint indica disponibilidad de la API; no verifica sus conexiones a las bases.
El endpoint `/api/health/databases` comprueba MongoDB y Neo4j por separado y devuelve
HTTP 200 si ambas responden o HTTP 503 si falla alguna; su JSON identifica cuál.

Para revisar la compilación local: `npm run preview --prefix frontend`, puerto 4173,
manteniendo FastAPI activo. No es un servidor de producción.

## Persistencia y detención

Detener únicamente los servidores propios de esta ejecución con `Ctrl+C`. Para
detener las bases de este proyecto conservando los datos:

```bash
docker compose stop
```

Los volúmenes llevan el prefijo `usac-nosql`. No ejecutar `docker compose down -v`:
eliminaría los volúmenes. No se deben borrar datos ni volúmenes sin autorización.

## Documentación y Git

Consultar [la explicación de la etapa 1](docs/etapa-1.md). `.gitignore` excluye
credenciales locales, `.venv`, `node_modules`, compilaciones y CSV originales.
Los archivos de dependencias y sus versiones sí se versionan.

Mensaje propuesto para el commit manual de esta etapa:

```text
feat: configurar conexiones a bases de datos NoSQL
```
