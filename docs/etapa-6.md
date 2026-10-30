# Etapa 6: frontend React y Vite

Implementado en `feature/react-dashboard`. La rama conserva el historial existente;
los cambios de la etapa 5 siguen pendientes junto con esta etapa, sin commits,
merges ni push. No se modificaron las bases ni se ejecutaron cargas nuevas.

## Ejecutar y visualizar

Desde la raíz, instalar exactamente las dependencias del lockfile:

```bash
npm ci --prefix frontend
```

Con MongoDB y Neo4j existentes activos, abrir dos terminales:

```bash
.venv/bin/python -m uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

```bash
npm run dev --prefix frontend
```

Abrir **http://127.0.0.1:5173**. Swagger permanece en http://127.0.0.1:8000/docs.
El navegador consulta rutas relativas /api y Vite las reenvía al backend. Ninguna
credencial de MongoDB o Neo4j se incluye en el bundle del navegador.

Si los puertos están ocupados, no detener procesos desconocidos. Utilizar puertos
alternativos en dos terminales:

```bash
.venv/bin/python -m uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8001
```

```bash
API_PROXY_TARGET=http://127.0.0.1:8001 FRONTEND_PORT=5174 npm run dev --prefix frontend
```

Abrir http://127.0.0.1:5174. También se pueden configurar las variables en
frontend/.env.local siguiendo frontend/.env.example, sin sobrescribir archivos
existentes. Son variables del servidor Vite, no secretos enviados a React.

Para compilar y revisar el bundle:

```bash
npm run build --prefix frontend
npm run preview --prefix frontend
```

Abrir http://127.0.0.1:4173 manteniendo FastAPI en 8000, o configurar
API_PROXY_TARGET para el puerto alternativo antes de iniciar preview. Preview es
una comprobación local, no un servidor de producción. El despliegue debe servir
index.html como fallback para las rutas BrowserRouter y reenviar /api a FastAPI.
No se cambia la configuración de hosting en esta etapa.

Requisitos existentes: Node.js 22.12 o superior dentro de la rama 22 y npm 10.
Las dependencias nuevas están fijadas con versiones exactas en package.json y
package-lock.json. Se conserva React y Vite; no se reemplaza el proyecto base.

## Pantallas y contratos reales

| Ruta React | Función | Endpoints |
| --- | --- | --- |
| / | Indicadores, evolución histórica y distribución | /api/estadisticas y /api/estadisticas/aprobacion |
| /estadisticas | Evolución, carreras y procedencia | /api/estadisticas/aprobacion, /api/resultados/carreras y /api/procedencia |
| /evaluaciones | Tabla, detalle y paginación por cursor | /api/evaluaciones |
| /grafo | Explorador interactivo y consulta de cohorte | /api/grafo y /api/grafo/aspirantes/{cohorte_id} |

Los filtros se construyen con /api/catalogos, cargado una vez por montaje de la
aplicación y compartido mediante contexto. El encabezado consulta
/api/health/databases y permite reintentar. Los mensajes de salud no sustituyen las
respuestas de los endpoints de cada sección.

| Sección | Filtros enviados |
| --- | --- |
| Indicadores y distribución | anio, materia, aprobado |
| Evolución histórica | desde, hasta |
| Carreras | anio obligatorio, materia |
| Procedencia | anio obligatorio |
| Evaluaciones | anio, materia, aprobado, limite, cursor |
| Grafo | anio obligatorio, materia, aprobado, carrera_id, limite |
| Vista de cohorte | cohorte_id, limite |

Carrera no filtra los indicadores ni la tabla: esos endpoints no la admiten.
Tampoco se envía aprobado a carreras o procedencia. En Estadísticas los parámetros
de URL tienen prefijos historico_, carrera_ y procedencia_ para que aplicar un
filtro no restablezca las otras secciones. En páginas con una sola selección los
parámetros usan los nombres habituales. Se puede recargar o compartir la URL y
conservar sus filtros; los cursores de las páginas visitadas quedan en memoria.

La serie histórica del Dashboard siempre representa 2015–2024 y todas las materias
y resultados; su alcance aparece explícito. No cambia con los filtros de los
indicadores. Para cambiar el rango histórico utilizar Estadísticas.

La procedencia se agrupa por departamento para dibujar las diez categorías con más
registros. La tabla conserva todos los grupos departamento/tipo recibidos. Las
restas registros-aprobados y las sumas por departamento son transformaciones de
presentación de valores reales, no datos simulados.

## Interacción y límites

Los filtros tienen borrador y botón Aplicar; no se ejecuta una consulta por cada
cambio de selector. Restablecer vuelve al alcance inicial. Los formularios de año
obligatorio y rangos requieren selección; las validaciones completas siguen en
FastAPI y sus errores se muestran sin reemplazar datos por cifras inventadas.

Evaluaciones utiliza páginas de 25, 50 o 100 registros. Siguiente emplea
siguiente_cursor; Anterior conserva los cursores visitados. Cambiar filtros o tamaño
reinicia la página y elimina su cursor efectivo. No se anuncia un número de páginas
que el backend no proporciona. El detalle muestra identidad de fuente, cohorte,
fecha de asignación, procedencia y advertencias.

El grafo comienza con 25 evaluaciones; permite solicitar 10, 25, 50 o 100. El backend
limita además la respuesta a 500 nodos y 800 relaciones. Se muestran los conteos
reales del subgrafo y el aviso de respuesta parcial cuando meta.truncado es true.
Esa selección por orden de id no es una muestra representativa del universo.

Cytoscape proporciona zoom, arrastre y selección; hay botones para acercar, alejar y
ajustar el encuadre. El inspector muestra propiedades del nodo seleccionado. Una
lista alternativa permite seleccionar nodos por teclado y consultar las relaciones
sin depender del canvas. Seleccionar Consultar esta cohorte utiliza su endpoint
específico y avisa que materia, resultado y carrera no se aplican en esa vista.
Volver a filtros recupera la selección original.

AspiranteCohorte siempre significa año + correlativo, no una persona global. La
fecha de asignación no es fecha de examen y convocatoria no es intento. La
procedencia educativa no es residencia. Las carreras recortadas se identifican
como tales y la ausencia se muestra como Sin información. MATEMATICA ITUGS se
conserva como materia independiente. No se reconstruyen datos de la fuente.

## Estructura y librerías

- components/layout: navegación responsive y estructura común.
- components/common: indicadores, contexto de catálogos y estados de consulta.
- components/filters: formulario reutilizable según el contrato de cada endpoint.
- components/charts: gráficas Recharts y tablas equivalentes.
- components/graph: canvas Cytoscape y ciclo de vida del motor.
- pages: Dashboard, Estadísticas, Evaluaciones y Grafo.
- hooks: consulta cancelable y sincronización de filtros con URL.
- services/api.js: fetch, errores JSON, timeout y codificación de parámetros.
- styles: base, estructura y componentes, sin librería visual adicional.
- tests y e2e: pruebas aisladas y navegador con el backend real.

React Router administra la navegación y la URL. Recharts dibuja gráficos de barras
y líneas. Cytoscape se importa solo al abrir el grafo. Las cuatro pantallas también
usan importación diferida; el build no necesita descargar el motor del grafo al
abrir el Dashboard. No se añadió Redux ni otro estado global de consultas.

El diseño conserva azul oscuro y dorado, incorpora verde petróleo para resultados
y utiliza tarjetas sobre fondo claro. Navegación lateral en escritorio y desplegable
en móvil, indicadores en dos columnas en pantallas estrechas, gráficos adaptables
y tablas con scroll propio. Se revisaron escritorio de 1440 px y móvil de 390 px,
sin desbordamiento horizontal global. Hay etiquetas explícitas, foco visible,
link de salto, estados anunciados, tablas alternativas y preferencia de movimiento
reducido. El grafo tiene selección alternativa por teclado, aunque el canvas por
sí solo no representa un árbol semántico accesible.

## Carga, errores y vacíos

Cada consulta conserva su estado loading/success/error. La carga no presenta ceros
como si fueran resultados recibidos. Las respuestas vacías tienen mensaje y opción
de restablecer filtros; un porcentaje null se muestra como Sin datos. El cliente
verifica el sobre JSON, conserva el contrato anterior de salud y presenta errores
seguros. No hay valores de respaldo para estadísticas cuando una consulta falla.

Timeout HTTP de 20 segundos. Al cambiar la URL de consulta o desmontar el componente
se cancela con AbortController y se ignoran respuestas atrasadas. Reintentar repite
la consulta actual. Un error de Neo4j no impide consultar las pantallas MongoDB.
Los catálogos y sus fallos también se gestionan explícitamente.

## Pruebas y resultados

```bash
npm test --prefix frontend
npm run build --prefix frontend
npm run test:e2e --prefix frontend
```

Vitest + Testing Library + jsdom: 13 pruebas correctas de codificación de filtros,
contratos JSON, errores, cancelación, indicadores nulos, carga/error/vacío, catálogos,
independencia de filtros, respuesta atrasada y reinicio de paginación.
Los datos mínimos de estas pruebas están dentro de los tests, nunca en la app.

Playwright: ocho pruebas correctas en Google Chrome real. Requiere Chrome instalado
y las bases existentes disponibles. Inicia servidores propios de FastAPI y Vite en
8010 y 5180, falla si ya están ocupados y los detiene al finalizar. No interfiere
con los servidores de desarrollo en 8000/5173. Las comprobaciones usan los endpoints
reales, sin sustituir estadísticas por fixtures:

1. Indicadores coinciden con /api/estadisticas; filtros año/materia/aprobado funcionan.
2. La tabla cambia de cursor, vuelve a la página anterior y reinicia al filtrar.
3. El grafo crea canvas, permite zoom, selección accesible y consulta de cohorte.
4. Navegación y visualización móvil sin desbordamiento horizontal global.
5. Fallo de red provocado y recuperación mediante Reintentar contra el servidor real.
6. Filtros de carreras e histórico conservan el año independiente de procedencia.
7. Grafo filtrado por materia, resultado y carrera de una evaluación real.
8. Año 2015 + MATEMATICA ITUGS devuelve vacío real y porcentaje Sin datos.

No se detectaron excepciones JavaScript en los ocho recorridos. El primer intento
reveló un selector exacto de etiqueta no reconocido: se corrigieron los nombres
accesibles de los controles y la suite completa pasó. Se eliminaron animaciones
iniciales de gráficos para dibujar los valores completos inmediatamente.

La compilación de producción completó sin advertencias de chunks grandes, con
pantallas y motores separados. También se ejecutó la regresión del backend con
consultas de solo lectura; sus resultados se detallan en etapa 5.
Capturas locales en data/reports/etapa-6: dashboard-desktop.png,
estadisticas-desktop.png, evaluaciones-desktop.png, grafo-desktop.png,
dashboard-mobile.png y grafo-mobile.png. Capturas, trazas y bundles se excluyen de
Git. No se incluyen CSV, secretos ni datos generados en los archivos del frontend.
