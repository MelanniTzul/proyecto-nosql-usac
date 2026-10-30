# Etapa 1: estructura inicial y Docker

## Arquitectura

```text
Navegador (React) → Vite /api → FastAPI
                                ↓ etapa 2
                          MongoDB y Neo4j
```

El frontend usa React con JavaScript. El proxy de Vite reenvía `/api` a FastAPI y
permite el flujo local sin configurar CORS. En producción habrá que configurar
el servidor que enrute esas solicitudes. React nunca recibirá credenciales de bases.

Los directorios se incorporan cuando tienen contenido útil. En etapas posteriores,
`core` contendrá configuración, `models` validación, `services` ETL y lógica analítica,
`database` conexiones, y `consultas` los pipelines MongoDB y las consultas Cypher.

## Archivos importantes

| Archivo | Responsabilidad |
| --- | --- |
| `backend/app/main.py` | Crea FastAPI y registra rutas bajo `/api` |
| `backend/app/api/health.py` | Endpoint y modelo Pydantic de respuesta |
| `backend/requirements.txt` | Dependencias directas y transitivas fijadas |
| `frontend/src/App.jsx` | Pantalla y estados de conexión |
| `frontend/src/services/api.js` | Petición fetch y validación de respuesta |
| `frontend/vite.config.js` | Proxy y puertos configurables |
| `frontend/src/styles.css` | Diseño adaptable y foco visible |
| `frontend/package-lock.json` | Árbol reproducible de dependencias npm |
| `docker-compose.yml` | Bases, puertos, autenticación, volúmenes y salud |
| `.env.example` y `frontend/.env.example` | Variables de ejemplo |
| `.gitignore` | Exclusión de archivos privados y generados |

## Recorrido de la petición

1. `App` ejecuta `useEffect` y cambia al estado de espera.
2. `getHealth` llama a `/api/health` con fetch.
3. Vite reenvía la solicitud a FastAPI.
4. El router devuelve una respuesta validada con Pydantic.
5. React muestra conexión o error; el botón permite repetir.

`AbortController` limita la espera y cancela solicitudes al desmontar el componente.
La variable `active` evita actualizar el estado desde efectos descartados, incluido
el ciclo adicional de desarrollo de `React.StrictMode`.

El healthcheck de MongoDB ejecuta un ping autenticado. El de Neo4j ejecuta
`RETURN 1` autenticado. Estos verifican las bases de forma independiente del backend.

## Límites de esta etapa

Todavía no hay conexiones de Python a las bases, CSV, ETL, métricas, consultas ni
grafos. La identidad de las evaluaciones, el alcance del correlativo, la edad
aproximada y el orden de intentos requieren inspeccionar los archivos originales.
Los campos esperados tampoco identifican una institución educativa concreta;
no se inventarán instituciones a partir de municipio y tipo.

## Plan de commits

1. Estructura inicial, comunicación React–FastAPI y Docker.
2. Conexiones reales a MongoDB y Neo4j.
3. Inspección CSV, ETL, carga y proyección mínima al grafo.
4. Veinte consultas MongoDB y `resumen_carrera`, accesibles desde React.
5. Modelo completo y cinco consultas Cypher.
6. Dashboard y visualizaciones.
7. Buscador, filtros y explorador de grafos.
8. Pruebas integrales, manuales y análisis de datos reales.

Cada etapa termina con comprobaciones y revisión antes del commit manual.

## Verificación realizada: 29 de octubre de 2026

| Comprobación | Resultado |
| --- | --- |
| `npm run build --prefix frontend` | Correcto; compilación de producción generada |
| `.venv/bin/python -m pip check` | Sin dependencias incompatibles |
| `docker compose config --quiet` | Configuración válida |
| FastAPI `/api/health` en 8000 y 8001 | HTTP 200 y JSON esperado |
| Proxy `/api/health` en 5173 y 5174 | HTTP 200 y JSON esperado |
| HTML del frontend en ambos puertos | Correcto |
| React ejecutado en Chrome headless, puerto 5173 | DOM con “API disponible” y nombre del servicio |
| MongoDB: ping autenticado | `{ ok: 1 }`, contenedor healthy |
| Neo4j: `RETURN 1 AS comprobacion` autenticado | Devuelve 1, contenedor healthy |
| Revisión de archivos candidatos a Git | 19 archivos; sin contraseñas de `.env` ni directorios generados |
| Índice de Git | Vacío; ningún archivo preparado para commit |

El fallo inicial al iniciar Vite fue `EPERM` por restricciones del entorno del
agente. La ejecución autorizada fuera de ese entorno inició correctamente.
La inspección posterior identificó que el puerto 8000 estaba ocupado por Uvicorn
de este mismo proyecto (PID 1094728); se reutilizó sin detenerlo. El puerto 5173
estaba libre. Una segunda instancia de FastAPI en 8001 y Vite en 5174 confirmó
que los puertos alternativos y `API_PROXY_TARGET` funcionan.

La validación inicial de Compose detectó un comando del healthcheck interpretado
como objeto YAML debido a `: `; se corrigió utilizando un bloque de texto y la
validación posterior pasó.

No se detuvieron servicios existentes ni se eliminaron volúmenes. Al finalizar
quedaron activos los servidores de desarrollo en 8000/5173 y los de prueba en
8001/5174. Los PID son evidencia de esta sesión y pueden cambiar.

La comprobación visual interactiva del botón de reintento, el estado de error y
los tamaños de pantalla queda pendiente de revisión manual. La prueba de Chrome
verificó ejecución de React y conexión correcta, no todas las interacciones.
No se probó todavía ninguna conexión desde FastAPI hacia las bases.
