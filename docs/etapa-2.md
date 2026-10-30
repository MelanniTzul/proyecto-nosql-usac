# Etapa 2: conexiones reales a MongoDB y Neo4j

## Decisiones técnicas

Se utiliza PyMongo para MongoDB y `neo4j` para Neo4j: ambos son controladores
oficiales. Se eligieron clientes síncronos para mantener el código comprensible.
FastAPI ejecuta el endpoint síncrono en su grupo de hilos, de modo que las esperas
de red no bloquean el bucle asíncrono del servidor.

`lifespan` crea una pareja de clientes por proceso al iniciar y los cierra al
terminar, incluso si se produce un error durante la ejecución. Los controladores
reutilizan conexiones mediante sus pools; no creamos clientes por solicitud.
Cada comprobación usa una sesión corta de Neo4j y la cierra al finalizar.

Los clientes conectan bajo demanda. Una base apagada no impide iniciar la API y
consultar su estado. Una configuración inválida, en cambio, impide iniciar con un
mensaje genérico, sin imprimir los valores recibidos.

## Archivos

| Archivo | Responsabilidad |
| --- | --- |
| `backend/app/core/config.py` | Lectura y validación de variables y secretos |
| `backend/app/database/connections.py` | Clientes, comprobaciones y cierre |
| `backend/app/main.py` | Ciclo de vida de los clientes en FastAPI |
| `backend/app/api/health.py` | Respuestas HTTP de disponibilidad |
| `backend/tests/test_database_health.py` | Pruebas contra bases reales, sin escrituras |
| `backend/requirements.txt` | Dependencias de ejecución fijadas |
| `backend/requirements-dev.txt` | Dependencias adicionales de pruebas |

## Configuración

La API lee automáticamente `.env` de la raíz del proyecto, usando su ruta absoluta,
incluso si se inicia desde `backend/`. Las variables del proceso tienen prioridad.
Conservar el `.env` existente: no copiar encima ni cambiar credenciales de bases
ya inicializadas. Si ya contiene las tres variables originales, no necesita cambios.

| Variable | Valor predeterminado o requisito |
| --- | --- |
| `MONGO_ROOT_USERNAME` | Obligatoria; usuario existente de Compose |
| `MONGO_ROOT_PASSWORD` | Obligatoria; contraseña existente |
| `MONGO_HOST` / `MONGO_PORT` | `127.0.0.1` / `27017` |
| `MONGO_AUTH_SOURCE` | `admin`, donde se autentica el usuario de Compose |
| `NEO4J_USERNAME` | `neo4j` |
| `NEO4J_PASSWORD` | Obligatoria; contraseña existente |
| `NEO4J_HOST` / `NEO4J_PORT` | `127.0.0.1` / `7687` |
| `NEO4J_DATABASE` | `neo4j` |
| `DB_TIMEOUT_SECONDS` | `3`, configurable entre 1 y 10 |

Los hosts aceptan nombres DNS o IPv4, sin esquema, puerto ni credenciales.
El backend local usa Bolt directo hacia la instancia Neo4j de Compose.
El transporte está pensado para desarrollo local; un despliegue remoto requerirá
configurar TLS y usuarios de aplicación con permisos específicos.

MongoDB recibe usuario y contraseña como argumentos separados: no construimos
una URI con credenciales ni necesitamos escapar caracteres de las contraseñas.
Pydantic utiliza `SecretStr` y oculta los valores en errores de validación. Las
respuestas no contienen URI, usuarios, contraseñas, excepciones ni trazas.
Los bloques de error no registran las excepciones de conexión.

## Iniciar

Desde la raíz:

```bash
.venv/bin/python -m pip install -r backend/requirements.txt
docker compose ps
.venv/bin/python -m uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

Si las bases existentes están detenidas, iniciarlas con `docker compose start`.
En una instalación nueva seguir el README. No eliminar ni recrear volúmenes.
Si hay un servidor anterior activo, no iniciar otro en el mismo puerto: usar un
puerto libre y ajustar `API_PROXY_TARGET` siguiendo el README.

En otra terminal:

```bash
npm run dev --prefix frontend
```

## Probar los endpoints

```bash
curl -i http://127.0.0.1:8000/api/health
curl -i http://127.0.0.1:8000/api/health/databases
curl -i http://127.0.0.1:5173/api/health/databases
```

`/api/health` conserva exactamente su contrato anterior: HTTP 200 con
`{"status":"ok","service":"usac-admisiones-api"}`. Confirma que la API está viva.

`/api/health/databases` ejecuta un ping autenticado a MongoDB y `RETURN 1` en la
base Neo4j seleccionada. No crea bases, colecciones, índices, nodos ni relaciones.
Cuando ambas funcionan devuelve HTTP 200:

```json
{
  "status": "ok",
  "mongodb": {"status": "ok", "message": "Conexión verificada."},
  "neo4j": {"status": "ok", "message": "Conexión verificada."}
}
```

Si falla alguna, devuelve HTTP 503 y `status: "error"` global. La base afectada
incluye `status: "error"` y `message: "No se pudo verificar la conexión."`.
La otra se comprueba igualmente. La respuesta usa `Cache-Control: no-store`.
Los timeouts limitan las esperas del controlador y Neo4j no reintenta transacciones;
no representan un límite global exacto para toda la petición: las comprobaciones
son secuenciales y el tiempo de DNS, conexión y consulta puede acumularse.

El ping y la consulta prueban autenticación y conectividad; no demuestran permisos
de escritura ni la corrección del futuro ETL. React conserva su comprobación actual
de la API; el nuevo endpoint es accesible también por su proxy.

## Pruebas de integración reproducibles

Con las bases activas y las credenciales locales correctas:

```bash
.venv/bin/python -m pip install -r backend/requirements-dev.txt
cd backend
../.venv/bin/python -m unittest discover -s tests -v
```

Las pruebas usan TestClient para las solicitudes HTTP a FastAPI, pero los clientes
de MongoDB y Neo4j se conectan realmente: no se sustituyen por mocks.
Se modifica únicamente el entorno temporal del proceso de pruebas. Las contraseñas
incorrectas provocan intentos fallidos de autenticación, sin cambiar usuarios.
Para comprobar indisponibilidad se reservan puertos locales sin escuchar; no se
detienen los servicios reales. Se capturan los logs, incluso a nivel DEBUG, y se
comprueba que ni los logs ni las respuestas HTTP contienen las contraseñas utilizadas.

Los casos cubren ambas bases disponibles, fallo independiente de autenticación de
cada base, ambas inaccesibles, disponibilidad de `/api/health` durante esos fallos,
configuración inválida sin filtración y carga de `.env` desde otro directorio.

## Resultados verificados el 30 de octubre de 2026

- Seis pruebas de integración correctas (`Ran 6 tests`, `OK`), sin mocks de bases.
- `/api/health` y `/api/health/databases`: HTTP 200 tanto en FastAPI (8000)
  como a través del proxy de Vite (5173). Ambas bases reportaron `ok`.
- MongoDB y Neo4j permanecieron `healthy`; no se recrearon contenedores ni volúmenes.
- React ejecutado en Chrome mostró “API disponible” y el nombre real del servicio.
- Compilación del frontend correcta y `pip check` sin incompatibilidades.
- Revisión de los 26 archivos versionados o candidatos: sin contraseñas locales
  ni directorios de herramientas, entornos o dependencias generadas. Índice Git vacío.

En la primera ejecución apareció un aviso de Starlette sobre el uso obsoleto de
`httpx` para TestClient. Se añadió `httpx2`, solicitado por la versión instalada,
a las dependencias de desarrollo; la segunda ejecución pasó sin ese aviso.
No quedan fallos en las pruebas de esta etapa. Las pruebas no cubren escrituras,
carga CSV ni consultas analíticas: corresponden a etapas posteriores.

## Git y alcance

Trabajo realizado en `feature/conexiones-nosql`, sin cambiar `main` ni `develop`.
No se ejecutan add, commit, push ni merge. `.env` y los entornos siguen excluidos.
Las dependencias se versionan como listas fijadas, no como carpetas instaladas.
El ETL continúa pendiente hasta inspeccionar los CSV reales.
