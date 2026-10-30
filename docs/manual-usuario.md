# Manual de usuario — Admisiones USAC

## 1. Acceso y propósito

La aplicación permite consultar pruebas específicas de admisión de Ingeniería USAC
correspondientes a los años de ingreso 2015–2024. Las estadísticas proceden de
MongoDB y las relaciones del explorador proceden de Neo4j. No permite editar,
importar ni eliminar información desde el navegador.

Con el proyecto iniciado, abrir **http://127.0.0.1:5173**. Si se usan puertos
alternativos, el responsable técnico debe indicar la dirección correspondiente.
Para instalar y arrancar el sistema consultar [README](../README.md) y el
[manual técnico](manual-tecnico.md). No se requiere iniciar sesión en la aplicación.

La navegación lateral contiene cuatro opciones. En una pantalla móvil se abre
con el botón de menú de la esquina superior izquierda. La opción activa queda
resaltada. El encabezado indica Bases disponibles cuando la comprobación de ambas
bases responde correctamente; el icono de recarga permite comprobar de nuevo.
Un problema de conexión se presenta con un mensaje, no con cifras de respaldo.

## 2. Resumen general

Abrir **Resumen general**. Se muestran cuatro indicadores:

- Total de evaluaciones: registros incluidos en la selección.
- Aprobadas: registros cuyo resultado es aprobado.
- No aprobadas: registros cuyo resultado es no aprobado.
- Porcentaje de aprobación: aprobadas / total de registros × 100.

La selección inicial incluye todos los años, materias y resultados. En la
instalación validada el conjunto completo tiene 208453 registros, 29877 aprobados,
178576 no aprobados y 14.33% de aprobación. La pantalla consulta esas cifras al
ser abierta; no contiene esos resultados como datos de demostración.

### Utilizar los filtros

1. Seleccionar Año de ingreso, Materia y/o Resultado.
2. Pulsar **Aplicar filtros** para realizar la consulta.
3. Esperar la respuesta antes de interpretar los valores.
4. Pulsar **Restablecer** para volver a todos los registros.

Las opciones de materia son Matemática, Computación y Matemática ITUGS, obtenidas
del catálogo real. Si se elige exclusivamente Aprobado, la tasa de esa selección
será 100% cuando existan registros; si se elige No aprobado será 0%. Esto describe
el subconjunto filtrado, no la tasa general de admisión. La nota bajo los indicadores
explica ese denominador. Cuando no hay registros, la tasa se muestra **Sin datos**.

### Leer las gráficas

Distribución de resultados corresponde a los filtros de los indicadores.
Evolución de la aprobación muestra la serie histórica completa 2015–2024 por materia;
su alcance aparece en el subtítulo y no cambia con esos filtros. Para escoger otro
rango histórico, utilizar Estadísticas. Pasar el cursor por un dato muestra su
valor; **Ver tabla de datos** permite leer los valores sin depender del gráfico.

Calidad y contexto muestra cuántos registros seleccionados contienen advertencias.
Estas advierten limitaciones de la fuente, no significan necesariamente que el
registro sea inválido. Los enlaces inferiores llevan a Evaluaciones y al grafo.

## 3. Estadísticas

Cada sección tiene filtros propios. Cambiar el año de Carreras no modifica el de
Procedencia ni el rango histórico. El estado de filtros se refleja en la URL,
por lo que se puede recargar o compartir la selección.

### Aprobación por año y materia

Seleccionar **Desde** y **Hasta**, y pulsar Aplicar filtros. El inicio no puede ser
posterior al final. La gráfica muestra porcentajes por grupo de año y materia;
**Ver tabla histórica** muestra las cantidades y porcentajes exactos. Restablecer
vuelve al rango 2015–2024. Un año ausente en una materia no se inventa como cero.

### Resultados por carrera

Seleccionar el año obligatorio y, opcionalmente, una materia. El año inicial es
2024. Pulsar Aplicar filtros. Las barras distinguen registros aprobados y no
aprobados; la tabla muestra carrera observada, estado, cantidad y aprobadas.

**Texto recortado** significa que la fuente no conserva el nombre completo. Una
carrera completa y una recortada con el mismo texto no se unen automáticamente.
**Sin información** identifica la ausencia de carrera. No representa una carrera
real adicional ni se elimina para mejorar los porcentajes.

Esta sección compara todas las carreras de esa selección; no tiene un selector
para filtrar los indicadores generales por carrera. El filtro por carrera está en
el Explorador de grafos, porque su endpoint sí lo admite.

### Procedencia educativa

Seleccionar un año y pulsar Aplicar filtros. La gráfica presenta los diez
departamentos con más registros, agregando sus tipos de institución. **Ver tabla
completa de procedencia** muestra todos los grupos departamento/tipo, incluidas
las ausencias. El año inicial es 2024.

La procedencia corresponde a la institución educativa informada; no indica dónde
reside la persona. No se identifican establecimientos concretos por nombre.

## 4. Evaluaciones

Abrir **Evaluaciones** para consultar registros individuales. Se puede filtrar por
año, materia y resultado. No existe filtro por carrera en esta pantalla.

La tabla presenta año, materia, convocatoria, resultado, carrera observada,
advertencias de calidad y el botón **Ver**. Este botón abre el detalle debajo de
la tabla, con identificador de fuente, aspirante de cohorte, fecha de asignación,
procedencia educativa y advertencias. **Cerrar** oculta ese detalle.

### Paginación

- Se muestran 25 registros por defecto; Por página permite 25, 50 o 100.
- **Siguiente** consulta la próxima página con el cursor recibido del servidor.
- **Anterior** vuelve a una página visitada durante esta sesión de pantalla.
- Los botones se deshabilitan cuando no corresponde avanzar o retroceder.
- Cambiar filtros o tamaño reinicia en la primera página.
- Al recargar la página se conservan los filtros de URL, no los cursores visitados.

No se anuncia un número total de páginas porque la API no lo proporciona. El orden
es por identificador de fuente, no por fecha o resultado. Los originales no se
modifican al consultar o abrir un detalle.

**Convocatoria no equivale a número de intento**, y fecha de asignación no es
necesariamente la fecha del examen. Aspirante de cohorte identifica año +
correlativo; no demuestra que dos años correspondan a la misma persona.

## 5. Explorador de grafos

Abrir **Explorador de grafos**. Seleccionar un año obligatorio y, opcionalmente,
materia, resultado y carrera observada. Elegir el tamaño del subgrafo: 10, 25, 50
o 100 evaluaciones. Pulsar Aplicar filtros. El inicio usa año 2024 y hasta 25
evaluaciones; Restablecer recupera esa selección.

La respuesta incluye evaluaciones y sus nodos relacionados, por lo que el número
de nodos es mayor que el de evaluaciones. El backend limita además la respuesta a
500 nodos y 800 relaciones. Los conteos que aparecen pertenecen al subgrafo, no a
toda la base.

### Interactuar

- Arrastrar el fondo para desplazarse y los nodos para reorganizarlos visualmente.
- Usar la rueda o los controles **+**, **−** y ajuste de encuadre para explorar.
- Seleccionar un nodo para consultar sus propiedades en el inspector.
- Consultar la leyenda de colores para distinguir los tipos.
- Abrir **Lista accesible de nodos y relaciones** para seleccionar con teclado y
  leer conexiones sin depender del canvas.

La posición o el tamaño visual de un nodo no indican probabilidad de aprobar ni
importancia académica. Arrastrar un nodo solo cambia su presentación en el navegador,
no sus datos ni relaciones almacenadas.

| Nodo | Significado |
| --- | --- |
| Evaluación | Ocurrencia de un registro publicado |
| Aspirante de cohorte | Agrupación por año y correlativo |
| Año de ingreso | Cohorte del registro |
| Materia | Materia informada de la prueba |
| Carrera observada | Valor publicado y su estado de normalización |
| Localidad educativa | Municipio/etiqueta observada con precisión de fuente |
| Departamento | Departamento educativo informado |
| Tipo de institución | Público, privado u otro tipo informado |

### Consultar un aspirante de cohorte

Seleccionar un nodo Aspirante de cohorte y pulsar **Consultar esta cohorte** en el
inspector. Esta vista consulta los registros de ese identificador dentro de su año.
El aviso superior aclara que materia, resultado y carrera no se aplican en esta
vista específica. **Volver a filtros** recupera el subgrafo anterior.

El mensaje **Subgrafo parcial** indica que existen más registros o se alcanzó un
límite. Ajustar los filtros para explorar otra selección. La selección por orden
de identificador no es una muestra estadísticamente representativa: sus proporciones
no deben interpretarse como tasas de toda la base.

## 6. Carga, respuestas vacías y errores

Durante una consulta aparece un indicador de carga. No interpretar la ausencia de
una tarjeta temporal como cero evaluaciones. **Sin resultados** significa que la
selección es válida pero no hay registros; se puede restablecer o cambiar filtros.
Un ejemplo real es Matemática ITUGS para 2015, materia que no aparece en ese año.

Ante un error aparece un mensaje y **Reintentar**. Revisar lo siguiente:

| Situación | Acción |
| --- | --- |
| No conecta con FastAPI | Pedir que se compruebe el backend y el proxy Vite |
| Servicio de base no disponible | Consultar el estado del encabezado y avisar al responsable técnico |
| Parámetros inválidos | Revisar años y filtros; Restablecer elimina una selección incorrecta |
| Consulta demasiado lenta | Reducir el tamaño del grafo o limitar la selección y reintentar |
| Selectores sin opciones | Esperar el catálogo o reintentar su consulta si aparece error |

Un error no se reemplaza con estadísticas inventadas. Si Neo4j no está disponible,
las consultas MongoDB pueden seguir funcionando. No intentar resolver errores
borrando bases, cambiando contraseñas o volviendo a cargar los CSV.

## 7. Interpretación y límites

El sistema cuenta registros de evaluación, incluidas repeticiones de la fuente.
No cuenta personas únicas de toda la década. Aprobar Matemática y Computación no
demuestra admisión definitiva. No se reconstruyen nombres recortados, zonas de
municipio ni escuelas. Los valores Sin información y las advertencias hacen visibles
esas limitaciones. Las pantallas son de consulta: no ofrecen edición ni exportación
de datos, y este manual no atribuye esas funciones al sistema.
