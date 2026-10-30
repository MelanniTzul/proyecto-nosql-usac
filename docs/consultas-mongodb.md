# 30 consultas MongoDB — Pruebas específicas de admisión USAC

## Alcance e inventario

Catálogo de 30 consultas distintas sobre `usac_admisiones.evaluaciones`, en la rama
`feature/consultas-mongodb`. El catálogo original se conserva; la integración posterior añade tres rutas
cerradas de ejecución sin cambiar contratos de las pantallas existentes, ETL o Neo4j. No se crean colecciones, índices ni resúmenes persistidos.

Las siete operaciones existentes de la API son válidas y se reutilizan directamente:
01 evaluations, 03 statistics, 05 approval, 09 careers, 15 provenance,
27 both_subjects y 30 catalogs. Su código permanece en
[ mongo_analytics.py ](../backend/app/services/mongo_analytics.py).
Las otras 23 entradas añaden un countDocuments y 22 pipelines. En conjunto se
cubren un find paginado, un countDocuments y 28 análisis de agregación, incluidos
los existentes; careers se reutiliza dentro de catalogs y no se cuenta dos veces.
Las funciones auxiliares, los cambios de parámetros y los conteos de verificación
no se presentan como consultas adicionales.

Se distinguen objetivos y dimensiones de agrupación, no solo filtros con otro año.
Todos los campos leídos existen en los documentos validados. Los nombres de campos
de salida son etiquetas calculadas; no se afirma que sean campos nuevos persistidos.

## Ejecución reproducible

Desde la raíz, con las dependencias y `.env` existentes:

```bash
PYTHONPATH=backend .venv/bin/python -m app.queries.mongodb --list
PYTHONPATH=backend .venv/bin/python -m app.queries.mongodb --all
PYTHONPATH=backend .venv/bin/python -m app.queries.mongodb --id 6 --output data/reports/consulta-06.json
```

`--list` no abre conexiones. `--all` ejecuta las 30 consultas secuencialmente,
verifica invariantes y escribe el reporte local `data/reports/consultas-mongodb.json`.
`--id` ejecuta una entrada; se puede elegir otro --output para conservar reportes.
El catálogo fuente está en [catalogo.json](../consultas/mongodb/catalogo.json) y el
intérprete en [mongodb.py](../backend/app/queries/mongodb.py). Ambos se versionan;
los resultados completos locales están excluidos de Git.

El intérprete solo admite operaciones de lectura y funciones existentes autorizadas.
Rechaza $out, $merge, $where y JavaScript de servidor. Los nuevos pipelines usan
maxTimeMS de 60000 y el CLI aplica un presupuesto cliente de 60 segundos por consulta.
Las funciones reutilizadas conservan además su maxTimeMS de API, por defecto 10
segundos. Este presupuesto de consola no cambia `.env` ni la configuración de la API.
La consulta 24 admite temporales internos de agregación con allowDiskUse; no escribe
resultados en colecciones ni modifica originales.

La primera prueba encontró NetworkTimeout en la consulta 24 con el límite de cliente
de 3 segundos; también fue insuficiente 10 segundos. Se añadió el contexto timeout
solo al CLI y se verificó la ejecución completa. No se alteraron datos para resolverlo.

## Preparación para ejecutar los fragmentos Python

Los bloques numerados son Python/PyMongo ejecutable, no pseudocódigo mongosh.
En una terminal `PYTHONPATH=backend .venv/bin/python`, preparar una sola conexión:

```python
from pymongo import timeout
from app.core.config import Settings
from app.database.connections import DatabaseConnections
from app.services import mongo_analytics as consultas
from app.models.analytics import (
    EvaluationFilters, Filters, RangeFilters, AnnualFilters, BothFilters,
)
conexiones = DatabaseConnections(Settings())
coleccion = conexiones.mongo["usac_admisiones"]["evaluaciones"]
```

Después ejecutar cualquiera de los bloques y, al terminar, `conexiones.close()`.
Se reutiliza la configuración y los clientes del proyecto; aunque DatabaseConnections
inicializa ambos controladores, estas consultas no envían operaciones a Neo4j.
No introducir contraseñas en los ejemplos ni modificar las bases para probarlos.
Para una ejecución completa con reporte, usar el CLI en lugar de pegar fragmentos.

## Resultados reales de la verificación

Estado: **completado**, 30/30 consultas correctas; tiempo total observado: **22.9969 segundos**.

Documentos antes: **208453**; después: **208453**.

Huella SHA-256 del catálogo verificado: `0497e5670f9edc9527803aeeabc2703f910a305a37a419de07d5d0c008daec13`.

Se comprobaron **31 invariantes**, todas correctas: las particiones anuales, por sexo, materia, carrera y procedencia reconstruyen el total; aprobados no supera registros; los histogramas reconstruyen las evaluaciones y cohortes.

El conteo estable no es por sí solo una prueba de identidad byte a byte: se revisan
también los operadores de lectura del catálogo y de las funciones reutilizadas.
No se ejecutan cargas ni operaciones de escritura. No se deben modificar fuentes
concurrentemente durante la verificación. Los tiempos son observaciones locales,
no garantías para otro equipo.

Cada sección muestra resultados reales completos cuando son pequeños y un extracto
explícito en listas largas. Los extractos no son totales. El reporte local conserva
todas las filas devueltas; límites y truncado se indican en 01 y 27.

| N.º | Consulta | Implementación |
| --- | --- | --- |
| 01 | Evaluaciones filtradas con paginación | Reutiliza API |
| 02 | Conteo total documental | countDocuments |
| 03 | Resumen general de aprobación y advertencias | Reutiliza API |
| 04 | Volumen anual de evaluaciones | aggregate |
| 05 | Aprobación por año y materia | Reutiliza API |
| 06 | Resultados por sexo informado | aggregate |
| 07 | Evolución anual de resultados por sexo | aggregate |
| 08 | Interacción materia y sexo | aggregate |
| 09 | Resultados por carrera observada | Reutiliza API |
| 10 | Evolución anual de carreras | aggregate |
| 11 | Materia y carrera observada | aggregate |
| 12 | Resultados por departamento educativo | aggregate |
| 13 | Municipios observados y precisión de la fuente | aggregate |
| 14 | Tipo de institución educativa | aggregate |
| 15 | Departamento y tipo educativo en 2024 | Reutiliza API |
| 16 | Sexo y tipo de institución | aggregate |
| 17 | Resultados por convocatoria y materia | aggregate |
| 18 | Actividad mensual de asignación | aggregate |
| 19 | Distribución de años de nacimiento conocidos | aggregate |
| 20 | Edad aproximada por año y materia | aggregate |
| 21 | Completitud de datos por cohorte | aggregate |
| 22 | Frecuencia de advertencias de calidad | aggregate |
| 23 | Carreras recortadas por cohorte y texto original | aggregate |
| 24 | Repeticiones exactas de la fuente | aggregate |
| 25 | Aspirantes de cohorte y carga de registros | aggregate |
| 26 | Histograma de registros por aspirante de cohorte | aggregate |
| 27 | Aprobación en ambas materias dentro de la cohorte | Reutiliza API |
| 28 | Múltiples carreras informadas dentro del año | aggregate |
| 29 | Coexistencia de resultados por cohorte y materia | aggregate |
| 30 | Catálogos reales con estado de carrera | Reutiliza API |

## 01. Evaluaciones filtradas con paginación

**Objetivo:** Consultar diez registros de Matemática no aprobados de 2024.

**Explicación:** Reutiliza find, proyección, orden y cursor de la API. Diez filas no representan el total de la selección.

**Código ejecutable:**

```python
with timeout(60):
    filas, siguiente_cursor = consultas.evaluations(conexiones, EvaluationFilters(**{'anio': 2024, 'materia': 'MATEMATICA', 'aprobado': False, 'limite': 10}))
resultado = {"registros": filas, "siguiente_cursor": siguiente_cursor, "limite": 10}
print(resultado)
```

**Verificación:** correcta; 0.0036 segundos. Se devolvieron 10 filas limitadas. Metadatos y extracto de las primeras 3:

```json
{
  "siguiente_cursor": "eyJpZCI6ICIwMDZjNzZiYjQwYTI5N2Q4M2I2ODlhNTZiNWUzMGY3OTFjNzQ1YTY5MzczMjY3MTlkYzJlN2Q4NjcwYmU2Y2JiIiwgImYiOiAiZTdiYmI4YTFkZDJiMDIyNGEwNTMzMmQ1ZmUxY2Y2MTc3NWEyZWI4ZGRkZDEzY2RlYTRhYTNkN2NhNTY1MTM3YSJ9",
  "limite": 10,
  "filas_devueltas": 10,
  "extracto_primeras_3": [
    {
      "anio_ingreso": 2024,
      "aprobado": false,
      "aspirante": {
        "cohorte_id": "2024:40e815b52f1f9d91a5ba",
        "sexo": "M",
        "anio_nacimiento": null
      },
      "carrera": {
        "valor": "INGENIERIA ELECTRICA",
        "estado_normalizacion": "completa"
      },
      "fecha_asignacion": "2023-10-11",
      "materia": "MATEMATICA",
      "numero_fecha_evaluacion": 3,
      "procedencia_educativa": {
        "departamento": "GUATEMALA",
        "municipio": "VILLA NUEVA",
        "tipo": "PRIVADO"
      },
      "id": "0001580c608abdfde98ce86fecd2dfc5c4f4a18819ffd2c3fbb0f1ec5f713d71",
      "advertencias": [
        "municipio: precision no garantizada por recorte de fuente"
      ]
    },
    {
      "anio_ingreso": 2024,
      "aprobado": false,
      "aspirante": {
        "cohorte_id": "2024:ea2f3c41f3e2f7ab036d7",
        "sexo": "M",
        "anio_nacimiento": 2006
      },
      "carrera": {
        "valor": "INGENIERIA EN CIENCIAS Y",
        "estado_normalizacion": "recortada"
      },
      "fecha_asignacion": "2023-08-04",
      "materia": "MATEMATICA",
      "numero_fecha_evaluacion": 1,
      "procedencia_educativa": {
        "departamento": "GUATEMALA",
        "municipio": "VILLA NUEVA",
        "tipo": "PRIVADO"
      },
      "id": "00133f510ac21a19098a323c620ea62b432919d37b75b9f3a698f80fbe743dd5",
      "advertencias": [
        "carrera_objetivo: valor recortado sin resolver",
        "municipio: precision no garantizada por recorte de fuente"
      ]
    },
    {
      "anio_ingreso": 2024,
      "aprobado": false,
      "aspirante": {
        "cohorte_id": "2024:cf09ac19e383c18ee9dc",
        "sexo": "M",
        "anio_nacimiento": 2004
      },
      "carrera": {
        "valor": "INGENIERIA MECANICA",
        "estado_normalizacion": "completa"
      },
      "fecha_asignacion": "2023-09-05",
      "materia": "MATEMATICA",
      "numero_fecha_evaluacion": 2,
      "procedencia_educativa": {
        "departamento": "CHIQUIMULA",
        "municipio": "ESQUIPULAS",
        "tipo": "PRIVADO"
      },
      "id": "001e34c03fb0b566fb3f988940b9dac42a9ec16f74b2a5e96fd1300d8cc886e6",
      "advertencias": [
        "municipio: precision no garantizada por recorte de fuente"
      ]
    }
  ]
}
```

## 02. Conteo total documental

**Objetivo:** Obtener el número exacto de ocurrencias almacenadas.

**Explicación:** countDocuments cuenta documentos; no personas globales ni evaluaciones deduplicadas.

**Código ejecutable:**

```python
with timeout(60):
    resultado = {"registros": coleccion.count_documents({}, maxTimeMS=60000)}
print(resultado)
```

**Verificación:** correcta; 0.1074 segundos. Resultado completo:

```json
{
  "registros": 208453
}
```

## 03. Resumen general de aprobación y advertencias

**Objetivo:** Calcular total, aprobados, no aprobados, tasa y filas advertidas.

**Explicación:** Reutiliza el agregado existente y su tratamiento de denominador cero. La tasa cuenta registros, no personas.

**Código ejecutable:**

```python
with timeout(60):
    resultado = consultas.statistics(conexiones, Filters(**{}))
print(resultado)
```

**Verificación:** correcta; 0.5424 segundos. Resultado completo:

```json
{
  "registros": 208453,
  "aprobados": 29877,
  "registros_con_advertencias": 56147,
  "no_aprobados": 178576,
  "porcentaje_aprobacion": 14.33
}
```

## 04. Volumen anual de evaluaciones

**Objetivo:** Comparar cuántos registros contiene cada cohorte.

**Explicación:** Agrupa por año de ingreso; no utiliza el año de asignación como sustituto.

**Código ejecutable:**

```python
pipeline = [{'$group': {'_id': '$anio_ingreso', 'registros': {'$sum': 1}}},
 {'$project': {'_id': 0, 'anio': '$_id', 'registros': 1}},
 {'$sort': {'anio': 1}}]
with timeout(60):
    resultado = list(coleccion.aggregate(
        pipeline, maxTimeMS=60000, allowDiskUse=False))
print(resultado)
```

**Verificación:** correcta; 0.0816 segundos. Se devolvieron 10 filas. Resultado completo:

```json
[
  {
    "registros": 20277,
    "anio": 2015
  },
  {
    "registros": 22137,
    "anio": 2016
  },
  {
    "registros": 21581,
    "anio": 2017
  },
  {
    "registros": 20871,
    "anio": 2018
  },
  {
    "registros": 17865,
    "anio": 2019
  },
  {
    "registros": 17931,
    "anio": 2020
  },
  {
    "registros": 30644,
    "anio": 2021
  },
  {
    "registros": 24237,
    "anio": 2022
  },
  {
    "registros": 19047,
    "anio": 2023
  },
  {
    "registros": 13863,
    "anio": 2024
  }
]
```

## 05. Aprobación por año y materia

**Objetivo:** Comparar la tasa de cada materia dentro de cada cohorte.

**Explicación:** Reutiliza approval con el rango completo. MATEMATICA ITUGS permanece separada.

**Código ejecutable:**

```python
with timeout(60):
    resultado = consultas.approval(conexiones, RangeFilters(**{'desde': 2015, 'hasta': 2024}))
print(resultado)
```

**Verificación:** correcta; 0.3192 segundos. Se devolvieron 22 filas. Extracto de las primeras 3 filas; no es el total:

```json
[
  {
    "anio": 2015,
    "materia": "COMPUTACION",
    "registros": 6730,
    "aprobados": 3352,
    "porcentaje": 49.81
  },
  {
    "anio": 2015,
    "materia": "MATEMATICA",
    "registros": 13547,
    "aprobados": 1397,
    "porcentaje": 10.31
  },
  {
    "anio": 2016,
    "materia": "COMPUTACION",
    "registros": 8395,
    "aprobados": 2028,
    "porcentaje": 24.16
  }
]
```

## 06. Resultados por sexo informado

**Objetivo:** Mostrar distribución y aprobación por sexo, incluyendo ausencias.

**Explicación:** Los valores nulos son una categoría explícita; no se imputa sexo.

**Código ejecutable:**

```python
pipeline = [{'$group': {'_id': {'sexo': '$aspirante.sexo'},
             'registros': {'$sum': 1},
             'aprobados': {'$sum': {'$cond': ['$aprobado', 1, 0]}}}},
 {'$project': {'_id': 0,
               'sexo': '$_id.sexo',
               'registros': 1,
               'aprobados': 1,
               'no_aprobados': {'$subtract': ['$registros', '$aprobados']},
               'porcentaje_aprobacion': {'$round': [{'$multiply': [{'$divide': ['$aprobados',
                                                                                '$registros']},
                                                                   100]},
                                                    2]}}},
 {'$sort': {'sexo': 1}}]
with timeout(60):
    resultado = list(coleccion.aggregate(
        pipeline, maxTimeMS=60000, allowDiskUse=False))
print(resultado)
```

**Verificación:** correcta; 0.1405 segundos. Se devolvieron 3 filas. Resultado completo:

```json
[
  {
    "registros": 188,
    "aprobados": 31,
    "sexo": null,
    "no_aprobados": 157,
    "porcentaje_aprobacion": 16.49
  },
  {
    "registros": 46304,
    "aprobados": 6064,
    "sexo": "F",
    "no_aprobados": 40240,
    "porcentaje_aprobacion": 13.1
  },
  {
    "registros": 161961,
    "aprobados": 23782,
    "sexo": "M",
    "no_aprobados": 138179,
    "porcentaje_aprobacion": 14.68
  }
]
```

## 07. Evolución anual de resultados por sexo

**Objetivo:** Comparar resultados por sexo dentro de cada año.

**Explicación:** El cruce año-sexo permite comparar cohortes sin confundir composición anual con el agregado global.

**Código ejecutable:**

```python
pipeline = [{'$group': {'_id': {'anio': '$anio_ingreso', 'sexo': '$aspirante.sexo'},
             'registros': {'$sum': 1},
             'aprobados': {'$sum': {'$cond': ['$aprobado', 1, 0]}}}},
 {'$project': {'_id': 0,
               'anio': '$_id.anio',
               'sexo': '$_id.sexo',
               'registros': 1,
               'aprobados': 1,
               'no_aprobados': {'$subtract': ['$registros', '$aprobados']},
               'porcentaje_aprobacion': {'$round': [{'$multiply': [{'$divide': ['$aprobados',
                                                                                '$registros']},
                                                                   100]},
                                                    2]}}},
 {'$sort': {'anio': 1, 'sexo': 1}}]
with timeout(60):
    resultado = list(coleccion.aggregate(
        pipeline, maxTimeMS=60000, allowDiskUse=False))
print(resultado)
```

**Verificación:** correcta; 0.1498 segundos. Se devolvieron 26 filas. Extracto de las primeras 3 filas; no es el total:

```json
[
  {
    "registros": 3877,
    "aprobados": 946,
    "anio": 2015,
    "sexo": "F",
    "no_aprobados": 2931,
    "porcentaje_aprobacion": 24.4
  },
  {
    "registros": 16400,
    "aprobados": 3803,
    "anio": 2015,
    "sexo": "M",
    "no_aprobados": 12597,
    "porcentaje_aprobacion": 23.19
  },
  {
    "registros": 4,
    "aprobados": 1,
    "anio": 2016,
    "sexo": null,
    "no_aprobados": 3,
    "porcentaje_aprobacion": 25.0
  }
]
```

## 08. Interacción materia y sexo

**Objetivo:** Comparar resultados de cada materia según sexo informado.

**Explicación:** Agrupa por dos dimensiones, conserva MATEMATICA ITUGS y sexo ausente.

**Código ejecutable:**

```python
pipeline = [{'$group': {'_id': {'materia': '$materia', 'sexo': '$aspirante.sexo'},
             'registros': {'$sum': 1},
             'aprobados': {'$sum': {'$cond': ['$aprobado', 1, 0]}}}},
 {'$project': {'_id': 0,
               'materia': '$_id.materia',
               'sexo': '$_id.sexo',
               'registros': 1,
               'aprobados': 1,
               'no_aprobados': {'$subtract': ['$registros', '$aprobados']},
               'porcentaje_aprobacion': {'$round': [{'$multiply': [{'$divide': ['$aprobados',
                                                                                '$registros']},
                                                                   100]},
                                                    2]}}},
 {'$sort': {'materia': 1, 'sexo': 1}}]
with timeout(60):
    resultado = list(coleccion.aggregate(
        pipeline, maxTimeMS=60000, allowDiskUse=False))
print(resultado)
```

**Verificación:** correcta; 0.1629 segundos. Se devolvieron 8 filas. Resultado completo:

```json
[
  {
    "registros": 91,
    "aprobados": 17,
    "materia": "COMPUTACION",
    "sexo": null,
    "no_aprobados": 74,
    "porcentaje_aprobacion": 18.68
  },
  {
    "registros": 19263,
    "aprobados": 3859,
    "materia": "COMPUTACION",
    "sexo": "F",
    "no_aprobados": 15404,
    "porcentaje_aprobacion": 20.03
  },
  {
    "registros": 64650,
    "aprobados": 14993,
    "materia": "COMPUTACION",
    "sexo": "M",
    "no_aprobados": 49657,
    "porcentaje_aprobacion": 23.19
  },
  {
    "registros": 97,
    "aprobados": 14,
    "materia": "MATEMATICA",
    "sexo": null,
    "no_aprobados": 83,
    "porcentaje_aprobacion": 14.43
  },
  {
    "registros": 27040,
    "aprobados": 2205,
    "materia": "MATEMATICA",
    "sexo": "F",
    "no_aprobados": 24835,
    "porcentaje_aprobacion": 8.15
  },
  {
    "registros": 97290,
    "aprobados": 8789,
    "materia": "MATEMATICA",
    "sexo": "M",
    "no_aprobados": 88501,
    "porcentaje_aprobacion": 9.03
  },
  {
    "registros": 1,
    "aprobados": 0,
    "materia": "MATEMATICA ITUGS",
    "sexo": "F",
    "no_aprobados": 1,
    "porcentaje_aprobacion": 0.0
  },
  {
    "registros": 21,
    "aprobados": 0,
    "materia": "MATEMATICA ITUGS",
    "sexo": "M",
    "no_aprobados": 21,
    "porcentaje_aprobacion": 0.0
  }
]
```

## 09. Resultados por carrera observada

**Objetivo:** Comparar todas las carreras por valor y estado de normalización.

**Explicación:** Reutiliza careers sin filtro anual. Una etiqueta completa y otra recortada nunca se fusionan.

**Código ejecutable:**

```python
with timeout(60):
    resultado = consultas.careers(conexiones)
print(resultado)
```

**Verificación:** correcta; 0.1725 segundos. Se devolvieron 16 filas. Extracto de las primeras 3 filas; no es el total:

```json
[
  {
    "id": "carrera:f6070b5a4c2b69c14d4d6bb9325c7475967423ab2ac73530d51585aa97da8bfb",
    "carrera": "INGENIERIA EN CIENCIAS Y SISTEMAS",
    "estado": "completa",
    "registros": 42427,
    "aprobados": 6533
  },
  {
    "id": "carrera:dbfd9b3c47260f28f1ff1eb65a11c88dc1f9d94bb4ed2f1204e6314a7d2009b9",
    "carrera": "INGENIERIA INDUSTRIAL",
    "estado": "completa",
    "registros": 28704,
    "aprobados": 3458
  },
  {
    "id": "carrera:b986db06a72c36cf432e23d63db9c9ed4424c4822514b66ab6402cd02e39d6f8",
    "carrera": "INGENIERIA CIVIL",
    "estado": "completa",
    "registros": 27638,
    "aprobados": 3174
  }
]
```

## 10. Evolución anual de carreras

**Objetivo:** Medir volumen y aprobación de cada categoría de carrera a través de los años.

**Explicación:** La clave contiene año, valor y estado; no reconstruye nombres truncados.

**Código ejecutable:**

```python
pipeline = [{'$group': {'_id': {'anio': '$anio_ingreso',
                     'carrera': '$carrera.valor',
                     'estado': '$carrera.estado_normalizacion'},
             'registros': {'$sum': 1},
             'aprobados': {'$sum': {'$cond': ['$aprobado', 1, 0]}}}},
 {'$project': {'_id': 0,
               'anio': '$_id.anio',
               'carrera': '$_id.carrera',
               'estado': '$_id.estado',
               'registros': 1,
               'aprobados': 1,
               'no_aprobados': {'$subtract': ['$registros', '$aprobados']},
               'porcentaje_aprobacion': {'$round': [{'$multiply': [{'$divide': ['$aprobados',
                                                                                '$registros']},
                                                                   100]},
                                                    2]}}},
 {'$sort': {'anio': 1, 'carrera': 1, 'estado': 1}}]
with timeout(60):
    resultado = list(coleccion.aggregate(
        pipeline, maxTimeMS=60000, allowDiskUse=False))
print(resultado)
```

**Verificación:** correcta; 0.2048 segundos. Se devolvieron 99 filas. Extracto de las primeras 3 filas; no es el total:

```json
[
  {
    "registros": 20275,
    "aprobados": 4749,
    "anio": 2015,
    "carrera": null,
    "estado": "ausente",
    "no_aprobados": 15526,
    "porcentaje_aprobacion": 23.42
  },
  {
    "registros": 2,
    "aprobados": 0,
    "anio": 2015,
    "carrera": "INGENIERIA EN CIENCIAS Y SISTEMAS",
    "estado": "completa",
    "no_aprobados": 2,
    "porcentaje_aprobacion": 0.0
  },
  {
    "registros": 462,
    "aprobados": 56,
    "anio": 2016,
    "carrera": "INGENIERIA AMBIENTAL",
    "estado": "completa",
    "no_aprobados": 406,
    "porcentaje_aprobacion": 12.12
  }
]
```

## 11. Materia y carrera observada

**Objetivo:** Identificar diferencias entre materias dentro de las categorías de carrera.

**Explicación:** Es un cruce materia-carrera, distinto de ordenar las carreras globales o cambiar solo un filtro.

**Código ejecutable:**

```python
pipeline = [{'$group': {'_id': {'materia': '$materia',
                     'carrera': '$carrera.valor',
                     'estado': '$carrera.estado_normalizacion'},
             'registros': {'$sum': 1},
             'aprobados': {'$sum': {'$cond': ['$aprobado', 1, 0]}}}},
 {'$project': {'_id': 0,
               'materia': '$_id.materia',
               'carrera': '$_id.carrera',
               'estado': '$_id.estado',
               'registros': 1,
               'aprobados': 1,
               'no_aprobados': {'$subtract': ['$registros', '$aprobados']},
               'porcentaje_aprobacion': {'$round': [{'$multiply': [{'$divide': ['$aprobados',
                                                                                '$registros']},
                                                                   100]},
                                                    2]}}},
 {'$sort': {'materia': 1, 'carrera': 1, 'estado': 1}}]
with timeout(60):
    resultado = list(coleccion.aggregate(
        pipeline, maxTimeMS=60000, allowDiskUse=False))
print(resultado)
```

**Verificación:** correcta; 0.2059 segundos. Se devolvieron 31 filas. Extracto de las primeras 3 filas; no es el total:

```json
[
  {
    "registros": 6730,
    "aprobados": 3352,
    "materia": "COMPUTACION",
    "carrera": null,
    "estado": "ausente",
    "no_aprobados": 3378,
    "porcentaje_aprobacion": 49.81
  },
  {
    "registros": 1132,
    "aprobados": 233,
    "materia": "COMPUTACION",
    "carrera": "INGENIERIA AMBIENTAL",
    "estado": "completa",
    "no_aprobados": 899,
    "porcentaje_aprobacion": 20.58
  },
  {
    "registros": 12249,
    "aprobados": 1946,
    "materia": "COMPUTACION",
    "carrera": "INGENIERIA CIVIL",
    "estado": "completa",
    "no_aprobados": 10303,
    "porcentaje_aprobacion": 15.89
  }
]
```

## 12. Resultados por departamento educativo

**Objetivo:** Comparar registros y tasas por departamento de la institución.

**Explicación:** No representa residencia y conserva el grupo nulo.

**Código ejecutable:**

```python
pipeline = [{'$group': {'_id': {'departamento': '$procedencia_educativa.departamento'},
             'registros': {'$sum': 1},
             'aprobados': {'$sum': {'$cond': ['$aprobado', 1, 0]}}}},
 {'$project': {'_id': 0,
               'departamento': '$_id.departamento',
               'registros': 1,
               'aprobados': 1,
               'no_aprobados': {'$subtract': ['$registros', '$aprobados']},
               'porcentaje_aprobacion': {'$round': [{'$multiply': [{'$divide': ['$aprobados',
                                                                                '$registros']},
                                                                   100]},
                                                    2]}}},
 {'$sort': {'registros': -1, 'departamento': 1}}]
with timeout(60):
    resultado = list(coleccion.aggregate(
        pipeline, maxTimeMS=60000, allowDiskUse=False))
print(resultado)
```

**Verificación:** correcta; 0.1544 segundos. Se devolvieron 24 filas. Extracto de las primeras 3 filas; no es el total:

```json
[
  {
    "registros": 159328,
    "aprobados": 23674,
    "departamento": "GUATEMALA",
    "no_aprobados": 135654,
    "porcentaje_aprobacion": 14.86
  },
  {
    "registros": 8807,
    "aprobados": 1152,
    "departamento": "CHIMALTENANGO",
    "no_aprobados": 7655,
    "porcentaje_aprobacion": 13.08
  },
  {
    "registros": 8591,
    "aprobados": 1209,
    "departamento": "SACATEPEQUEZ",
    "no_aprobados": 7382,
    "porcentaje_aprobacion": 14.07
  }
]
```

## 13. Municipios observados y precisión de la fuente

**Objetivo:** Analizar etiquetas de municipio dentro de su departamento y nivel de precisión.

**Explicación:** Separa 2022–2024 por precisión no garantizada; no reconstruye zonas ni escuelas.

**Código ejecutable:**

```python
pipeline = [{'$group': {'_id': {'departamento': '$procedencia_educativa.departamento',
                     'municipio': '$procedencia_educativa.municipio',
                     'precision': {'$cond': [{'$gte': ['$anio_ingreso', 2022]},
                                             'no_garantizada',
                                             'etiqueta_publicada']}},
             'registros': {'$sum': 1},
             'aprobados': {'$sum': {'$cond': ['$aprobado', 1, 0]}}}},
 {'$project': {'_id': 0,
               'departamento': '$_id.departamento',
               'municipio': '$_id.municipio',
               'precision': '$_id.precision',
               'registros': 1,
               'aprobados': 1,
               'no_aprobados': {'$subtract': ['$registros', '$aprobados']},
               'porcentaje_aprobacion': {'$round': [{'$multiply': [{'$divide': ['$aprobados',
                                                                                '$registros']},
                                                                   100]},
                                                    2]}}},
 {'$sort': {'registros': -1, 'departamento': 1, 'municipio': 1, 'precision': 1}}]
with timeout(60):
    resultado = list(coleccion.aggregate(
        pipeline, maxTimeMS=60000, allowDiskUse=False))
print(resultado)
```

**Verificación:** correcta; 0.2197 segundos. Se devolvieron 450 filas. Extracto de las primeras 3 filas; no es el total:

```json
[
  {
    "registros": 25579,
    "aprobados": 2918,
    "departamento": "GUATEMALA",
    "municipio": "GUATEMALA - CIUDAD",
    "precision": "no_garantizada",
    "no_aprobados": 22661,
    "porcentaje_aprobacion": 11.41
  },
  {
    "registros": 21208,
    "aprobados": 3081,
    "departamento": "GUATEMALA",
    "municipio": "GUATEMALA - CIUDAD CAPITAL ZONA 1",
    "precision": "etiqueta_publicada",
    "no_aprobados": 18127,
    "porcentaje_aprobacion": 14.53
  },
  {
    "registros": 18838,
    "aprobados": 3325,
    "departamento": "GUATEMALA",
    "municipio": "MIXCO",
    "precision": "etiqueta_publicada",
    "no_aprobados": 15513,
    "porcentaje_aprobacion": 17.65
  }
]
```

## 14. Tipo de institución educativa

**Objetivo:** Comparar aprobación y volumen entre tipos educativos.

**Explicación:** Público, privado, cooperativa, municipal y ausencia se mantienen como categorías de fuente.

**Código ejecutable:**

```python
pipeline = [{'$group': {'_id': {'tipo': '$procedencia_educativa.tipo'},
             'registros': {'$sum': 1},
             'aprobados': {'$sum': {'$cond': ['$aprobado', 1, 0]}}}},
 {'$project': {'_id': 0,
               'tipo': '$_id.tipo',
               'registros': 1,
               'aprobados': 1,
               'no_aprobados': {'$subtract': ['$registros', '$aprobados']},
               'porcentaje_aprobacion': {'$round': [{'$multiply': [{'$divide': ['$aprobados',
                                                                                '$registros']},
                                                                   100]},
                                                    2]}}},
 {'$sort': {'registros': -1, 'tipo': 1}}]
with timeout(60):
    resultado = list(coleccion.aggregate(
        pipeline, maxTimeMS=60000, allowDiskUse=False))
print(resultado)
```

**Verificación:** correcta; 0.1702 segundos. Se devolvieron 5 filas. Resultado completo:

```json
[
  {
    "registros": 172790,
    "aprobados": 25951,
    "tipo": "PRIVADO",
    "no_aprobados": 146839,
    "porcentaje_aprobacion": 15.02
  },
  {
    "registros": 28992,
    "aprobados": 3403,
    "tipo": "PUBLICO",
    "no_aprobados": 25589,
    "porcentaje_aprobacion": 11.74
  },
  {
    "registros": 4005,
    "aprobados": 231,
    "tipo": null,
    "no_aprobados": 3774,
    "porcentaje_aprobacion": 5.77
  },
  {
    "registros": 2381,
    "aprobados": 269,
    "tipo": "POR COOPERATIVA",
    "no_aprobados": 2112,
    "porcentaje_aprobacion": 11.3
  },
  {
    "registros": 285,
    "aprobados": 23,
    "tipo": "MUNICIPAL",
    "no_aprobados": 262,
    "porcentaje_aprobacion": 8.07
  }
]
```

## 15. Departamento y tipo educativo en 2024

**Objetivo:** Analizar conjuntamente departamento y tipo dentro de la cohorte 2024.

**Explicación:** Reutiliza provenance; incluye el grupo ausente que no genera relaciones en Cypher 06.

**Código ejecutable:**

```python
with timeout(60):
    resultado = consultas.provenance(conexiones, AnnualFilters(**{'anio': 2024}))
print(resultado)
```

**Verificación:** correcta; 0.0223 segundos. Se devolvieron 59 filas. Extracto de las primeras 3 filas; no es el total:

```json
[
  {
    "departamento": "GUATEMALA",
    "tipo": "PRIVADO",
    "registros": 8935,
    "aprobados": 1463
  },
  {
    "departamento": "GUATEMALA",
    "tipo": "PUBLICO",
    "registros": 1215,
    "aprobados": 169
  },
  {
    "departamento": "CHIMALTENANGO",
    "tipo": "PRIVADO",
    "registros": 529,
    "aprobados": 95
  }
]
```

## 16. Sexo y tipo de institución

**Objetivo:** Comparar resultados por sexo dentro de cada sector educativo.

**Explicación:** Permite observar composición de dos dimensiones sin inferir causalidad ni completar datos faltantes.

**Código ejecutable:**

```python
pipeline = [{'$group': {'_id': {'sexo': '$aspirante.sexo', 'tipo': '$procedencia_educativa.tipo'},
             'registros': {'$sum': 1},
             'aprobados': {'$sum': {'$cond': ['$aprobado', 1, 0]}}}},
 {'$project': {'_id': 0,
               'sexo': '$_id.sexo',
               'tipo': '$_id.tipo',
               'registros': 1,
               'aprobados': 1,
               'no_aprobados': {'$subtract': ['$registros', '$aprobados']},
               'porcentaje_aprobacion': {'$round': [{'$multiply': [{'$divide': ['$aprobados',
                                                                                '$registros']},
                                                                   100]},
                                                    2]}}},
 {'$sort': {'sexo': 1, 'tipo': 1}}]
with timeout(60):
    resultado = list(coleccion.aggregate(
        pipeline, maxTimeMS=60000, allowDiskUse=False))
print(resultado)
```

**Verificación:** correcta; 0.1676 segundos. Se devolvieron 12 filas. Extracto de las primeras 3 filas; no es el total:

```json
[
  {
    "registros": 155,
    "aprobados": 27,
    "sexo": null,
    "tipo": null,
    "no_aprobados": 128,
    "porcentaje_aprobacion": 17.42
  },
  {
    "registros": 33,
    "aprobados": 4,
    "sexo": null,
    "tipo": "PRIVADO",
    "no_aprobados": 29,
    "porcentaje_aprobacion": 12.12
  },
  {
    "registros": 994,
    "aprobados": 53,
    "sexo": "F",
    "tipo": null,
    "no_aprobados": 941,
    "porcentaje_aprobacion": 5.33
  }
]
```

## 17. Resultados por convocatoria y materia

**Objetivo:** Describir la distribución de aprobación por número de convocatoria y materia.

**Explicación:** Convocatoria no equivale a intento individual; se incluye el resultado booleano como dimensión.

**Código ejecutable:**

```python
pipeline = [{'$group': {'_id': {'convocatoria': '$numero_fecha_evaluacion',
                     'materia': '$materia',
                     'aprobado': '$aprobado'},
             'registros': {'$sum': 1}}},
 {'$project': {'_id': 0,
               'convocatoria': '$_id.convocatoria',
               'materia': '$_id.materia',
               'aprobado': '$_id.aprobado',
               'registros': 1}},
 {'$sort': {'convocatoria': 1, 'materia': 1, 'aprobado': 1}}]
with timeout(60):
    resultado = list(coleccion.aggregate(
        pipeline, maxTimeMS=60000, allowDiskUse=False))
print(resultado)
```

**Verificación:** correcta; 0.1242 segundos. Se devolvieron 24 filas. Extracto de las primeras 3 filas; no es el total:

```json
[
  {
    "registros": 19561,
    "convocatoria": 1,
    "materia": "COMPUTACION",
    "aprobado": false
  },
  {
    "registros": 5468,
    "convocatoria": 1,
    "materia": "COMPUTACION",
    "aprobado": true
  },
  {
    "registros": 31570,
    "convocatoria": 1,
    "materia": "MATEMATICA",
    "aprobado": false
  }
]
```

## 18. Actividad mensual de asignación

**Objetivo:** Observar el volumen publicado por mes de asignación.

**Explicación:** Extrae YYYY-MM de la cadena ISO validada. No afirma que ese mes sea el del examen ni el año de ingreso.

**Código ejecutable:**

```python
pipeline = [{'$group': {'_id': {'$substrBytes': ['$fecha_asignacion', 0, 7]}, 'registros': {'$sum': 1}}},
 {'$project': {'_id': 0, 'mes_asignacion': '$_id', 'registros': 1}},
 {'$sort': {'mes_asignacion': 1}}]
with timeout(60):
    resultado = list(coleccion.aggregate(
        pipeline, maxTimeMS=60000, allowDiskUse=False))
print(resultado)
```

**Verificación:** correcta; 0.2775 segundos. Se devolvieron 49 filas. Extracto de las primeras 3 filas; no es el total:

```json
[
  {
    "registros": 7000,
    "mes_asignacion": "2014-08"
  },
  {
    "registros": 4652,
    "mes_asignacion": "2014-09"
  },
  {
    "registros": 3853,
    "mes_asignacion": "2014-10"
  }
]
```

## 19. Distribución de años de nacimiento conocidos

**Objetivo:** Contar registros por año de nacimiento informado.

**Explicación:** Excluye nulos; el valor 1900 se conserva como dato publicado y no se convierte automáticamente a ausencia.

**Código ejecutable:**

```python
pipeline = [{'$match': {'aspirante.anio_nacimiento': {'$ne': None}}},
 {'$group': {'_id': '$aspirante.anio_nacimiento', 'registros': {'$sum': 1}}},
 {'$project': {'_id': 0, 'anio_nacimiento': '$_id', 'registros': 1}},
 {'$sort': {'anio_nacimiento': 1}}]
with timeout(60):
    resultado = list(coleccion.aggregate(
        pipeline, maxTimeMS=60000, allowDiskUse=False))
print(resultado)
```

**Verificación:** correcta; 0.1484 segundos. Se devolvieron 49 filas. Extracto de las primeras 3 filas; no es el total:

```json
[
  {
    "registros": 4,
    "anio_nacimiento": 1900
  },
  {
    "registros": 13,
    "anio_nacimiento": 1955
  },
  {
    "registros": 2,
    "anio_nacimiento": 1956
  }
]
```

## 20. Edad aproximada por año y materia

**Objetivo:** Describir edad aproximada a la asignación cuando nacimiento está informado.

**Explicación:** Resta año de asignación menos nacimiento: no es edad exacta. Para este resumen se restringe a 12–80 años; se informa cuántos registros se incluyen.

**Código ejecutable:**

```python
pipeline = [{'$match': {'aspirante.anio_nacimiento': {'$ne': None}}},
 {'$project': {'anio': '$anio_ingreso',
               'materia': 1,
               'edad_aproximada': {'$subtract': [{'$toInt': {'$substrBytes': ['$fecha_asignacion',
                                                                              0,
                                                                              4]}},
                                                 '$aspirante.anio_nacimiento']}}},
 {'$match': {'edad_aproximada': {'$gte': 12, '$lte': 80}}},
 {'$group': {'_id': {'anio': '$anio', 'materia': '$materia'},
             'registros_incluidos': {'$sum': 1},
             'edad_minima': {'$min': '$edad_aproximada'},
             'edad_maxima': {'$max': '$edad_aproximada'},
             'edad_media': {'$avg': '$edad_aproximada'}}},
 {'$project': {'_id': 0,
               'anio': '$_id.anio',
               'materia': '$_id.materia',
               'registros_incluidos': 1,
               'edad_minima': 1,
               'edad_maxima': 1,
               'edad_media': {'$round': ['$edad_media', 2]}}},
 {'$sort': {'anio': 1, 'materia': 1}}]
with timeout(60):
    resultado = list(coleccion.aggregate(
        pipeline, maxTimeMS=60000, allowDiskUse=False))
print(resultado)
```

**Verificación:** correcta; 0.9031 segundos. Se devolvieron 22 filas. Extracto de las primeras 3 filas; no es el total:

```json
[
  {
    "registros_incluidos": 1968,
    "edad_minima": 14,
    "edad_maxima": 42,
    "anio": 2015,
    "materia": "COMPUTACION",
    "edad_media": 19.92
  },
  {
    "registros_incluidos": 4115,
    "edad_minima": 14,
    "edad_maxima": 43,
    "anio": 2015,
    "materia": "MATEMATICA",
    "edad_media": 20.09
  },
  {
    "registros_incluidos": 7010,
    "edad_minima": 15,
    "edad_maxima": 61,
    "anio": 2016,
    "materia": "COMPUTACION",
    "edad_media": 19.42
  }
]
```

## 21. Completitud de datos por cohorte

**Objetivo:** Cuantificar ausencias por campo dentro de cada año.

**Explicación:** Cuenta nulos normalizados sin reemplazarlos. Las ausencias por campo pueden coexistir en la misma fila.

**Código ejecutable:**

```python
pipeline = [{'$group': {'_id': '$anio_ingreso',
             'registros': {'$sum': 1},
             'nacimiento_ausente': {'$sum': {'$cond': [{'$eq': ['$aspirante.anio_nacimiento',
                                                                None]},
                                                       1,
                                                       0]}},
             'sexo_ausente': {'$sum': {'$cond': [{'$eq': ['$aspirante.sexo', None]}, 1, 0]}},
             'carrera_ausente': {'$sum': {'$cond': [{'$eq': ['$carrera.valor', None]}, 1, 0]}},
             'departamento_ausente': {'$sum': {'$cond': [{'$eq': ['$procedencia_educativa.departamento',
                                                                  None]},
                                                         1,
                                                         0]}},
             'municipio_ausente': {'$sum': {'$cond': [{'$eq': ['$procedencia_educativa.municipio',
                                                               None]},
                                                      1,
                                                      0]}},
             'tipo_ausente': {'$sum': {'$cond': [{'$eq': ['$procedencia_educativa.tipo',
                                                          None]},
                                                 1,
                                                 0]}}}},
 {'$project': {'_id': 0,
               'anio': '$_id',
               'registros': 1,
               'nacimiento_ausente': 1,
               'sexo_ausente': 1,
               'carrera_ausente': 1,
               'departamento_ausente': 1,
               'municipio_ausente': 1,
               'tipo_ausente': 1,
               'porcentaje_sin_nacimiento': {'$round': [{'$multiply': [{'$divide': ['$nacimiento_ausente',
                                                                                    '$registros']},
                                                                       100]},
                                                        2]}}},
 {'$sort': {'anio': 1}}]
with timeout(60):
    resultado = list(coleccion.aggregate(
        pipeline, maxTimeMS=60000, allowDiskUse=False))
print(resultado)
```

**Verificación:** correcta; 0.3566 segundos. Se devolvieron 10 filas. Resultado completo:

```json
[
  {
    "registros": 20277,
    "nacimiento_ausente": 14192,
    "sexo_ausente": 0,
    "carrera_ausente": 20275,
    "departamento_ausente": 24,
    "municipio_ausente": 24,
    "tipo_ausente": 24,
    "anio": 2015,
    "porcentaje_sin_nacimiento": 69.99
  },
  {
    "registros": 22137,
    "nacimiento_ausente": 3790,
    "sexo_ausente": 4,
    "carrera_ausente": 0,
    "departamento_ausente": 22,
    "municipio_ausente": 22,
    "tipo_ausente": 22,
    "anio": 2016,
    "porcentaje_sin_nacimiento": 17.12
  },
  {
    "registros": 21581,
    "nacimiento_ausente": 370,
    "sexo_ausente": 13,
    "carrera_ausente": 0,
    "departamento_ausente": 105,
    "municipio_ausente": 105,
    "tipo_ausente": 105,
    "anio": 2017,
    "porcentaje_sin_nacimiento": 1.71
  },
  {
    "registros": 20871,
    "nacimiento_ausente": 285,
    "sexo_ausente": 29,
    "carrera_ausente": 0,
    "departamento_ausente": 126,
    "municipio_ausente": 126,
    "tipo_ausente": 126,
    "anio": 2018,
    "porcentaje_sin_nacimiento": 1.37
  },
  {
    "registros": 17865,
    "nacimiento_ausente": 224,
    "sexo_ausente": 29,
    "carrera_ausente": 0,
    "departamento_ausente": 210,
    "municipio_ausente": 210,
    "tipo_ausente": 210,
    "anio": 2019,
    "porcentaje_sin_nacimiento": 1.25
  },
  {
    "registros": 17931,
    "nacimiento_ausente": 241,
    "sexo_ausente": 55,
    "carrera_ausente": 0,
    "departamento_ausente": 545,
    "municipio_ausente": 545,
    "tipo_ausente": 545,
    "anio": 2020,
    "porcentaje_sin_nacimiento": 1.34
  },
  {
    "registros": 30644,
    "nacimiento_ausente": 216,
    "sexo_ausente": 58,
    "carrera_ausente": 0,
    "departamento_ausente": 1131,
    "municipio_ausente": 1131,
    "tipo_ausente": 1131,
    "anio": 2021,
    "porcentaje_sin_nacimiento": 0.7
  },
  {
    "registros": 24237,
    "nacimiento_ausente": 73,
    "sexo_ausente": 0,
    "carrera_ausente": 0,
    "departamento_ausente": 786,
    "municipio_ausente": 786,
    "tipo_ausente": 786,
    "anio": 2022,
    "porcentaje_sin_nacimiento": 0.3
  },
  {
    "registros": 19047,
    "nacimiento_ausente": 45,
    "sexo_ausente": 0,
    "carrera_ausente": 0,
    "departamento_ausente": 571,
    "municipio_ausente": 571,
    "tipo_ausente": 571,
    "anio": 2023,
    "porcentaje_sin_nacimiento": 0.24
  },
  {
    "registros": 13863,
    "nacimiento_ausente": 15,
    "sexo_ausente": 0,
    "carrera_ausente": 0,
    "departamento_ausente": 485,
    "municipio_ausente": 485,
    "tipo_ausente": 485,
    "anio": 2024,
    "porcentaje_sin_nacimiento": 0.11
  }
]
```

## 22. Frecuencia de advertencias de calidad

**Objetivo:** Identificar cuáles advertencias afectan más registros.

**Explicación:** Descompone la lista con $unwind. Una fila con varias advertencias contribuye a varias categorías, no a personas distintas.

**Código ejecutable:**

```python
pipeline = [{'$unwind': '$calidad.advertencias'},
 {'$group': {'_id': '$calidad.advertencias', 'registros': {'$sum': 1}}},
 {'$project': {'_id': 0, 'advertencia': '$_id', 'registros': 1}},
 {'$sort': {'registros': -1, 'advertencia': 1}}]
with timeout(60):
    resultado = list(coleccion.aggregate(
        pipeline, maxTimeMS=60000, allowDiskUse=False))
print(resultado)
```

**Verificación:** correcta; 0.4799 segundos. Se devolvieron 3 filas. Resultado completo:

```json
[
  {
    "registros": 55305,
    "advertencia": "municipio: precision no garantizada por recorte de fuente"
  },
  {
    "registros": 28010,
    "advertencia": "carrera_objetivo: valor recortado sin resolver"
  },
  {
    "registros": 4,
    "advertencia": "anio_nacimiento: edad aproximada atipica"
  }
]
```

## 23. Carreras recortadas por cohorte y texto original

**Objetivo:** Medir la pérdida de precisión conservando el texto original.

**Explicación:** Muestra original y normalizado, incluidos espacios de origen. No asigna equivalencias de carrera.

**Código ejecutable:**

```python
pipeline = [{'$match': {'carrera.estado_normalizacion': 'recortada'}},
 {'$group': {'_id': {'anio': '$anio_ingreso',
                     'original': '$originales.carrera_objetivo',
                     'normalizado': '$carrera.valor'},
             'registros': {'$sum': 1}}},
 {'$project': {'_id': 0,
               'anio': '$_id.anio',
               'original': '$_id.original',
               'normalizado': '$_id.normalizado',
               'registros': 1}},
 {'$sort': {'anio': 1, 'original': 1}}]
with timeout(60):
    resultado = list(coleccion.aggregate(
        pipeline, maxTimeMS=60000, allowDiskUse=False))
print(resultado)
```

**Verificación:** correcta; 0.1447 segundos. Se devolvieron 6 filas. Resultado completo:

```json
[
  {
    "registros": 9781,
    "anio": 2022,
    "original": "INGENIERIA EN CIENCIAS Y ",
    "normalizado": "INGENIERIA EN CIENCIAS Y"
  },
  {
    "registros": 1707,
    "anio": 2022,
    "original": "INGENIERIA MECANICA ",
    "normalizado": "INGENIERIA MECANICA"
  },
  {
    "registros": 8247,
    "anio": 2023,
    "original": "INGENIERIA EN CIENCIAS Y ",
    "normalizado": "INGENIERIA EN CIENCIAS Y"
  },
  {
    "registros": 1256,
    "anio": 2023,
    "original": "INGENIERIA MECANICA ",
    "normalizado": "INGENIERIA MECANICA"
  },
  {
    "registros": 6193,
    "anio": 2024,
    "original": "INGENIERIA EN CIENCIAS Y ",
    "normalizado": "INGENIERIA EN CIENCIAS Y"
  },
  {
    "registros": 826,
    "anio": 2024,
    "original": "INGENIERIA MECANICA ",
    "normalizado": "INGENIERIA MECANICA"
  }
]
```

## 24. Repeticiones exactas de la fuente

**Objetivo:** Contar grupos de filas originales idénticas y ocurrencias adicionales dentro de cada archivo.

**Explicación:** Agrupa las doce columnas originales junto con la huella de archivo. No elimina duplicados ni equipara una repetición a un examen duplicado demostrado.

**Código ejecutable:**

```python
pipeline = [{'$group': {'_id': {'archivo_sha256': '$fuente.sha256_archivo', 'originales': '$originales'},
             'ocurrencias': {'$sum': 1}}},
 {'$match': {'ocurrencias': {'$gt': 1}}},
 {'$group': {'_id': None,
             'grupos_repetidos': {'$sum': 1},
             'ocurrencias_adicionales': {'$sum': {'$subtract': ['$ocurrencias', 1]}},
             'maxima_multiplicidad': {'$max': '$ocurrencias'}}},
 {'$project': {'_id': 0,
               'grupos_repetidos': 1,
               'ocurrencias_adicionales': 1,
               'maxima_multiplicidad': 1}}]
with timeout(60):
    resultado = list(coleccion.aggregate(
        pipeline, maxTimeMS=60000, allowDiskUse=True))
print(resultado)
```

**Verificación:** correcta; 14.1805 segundos. Se devolvieron 1 filas. Resultado completo:

```json
[
  {
    "grupos_repetidos": 805,
    "ocurrencias_adicionales": 834,
    "maxima_multiplicidad": 6
  }
]
```

## 25. Aspirantes de cohorte y carga de registros

**Objetivo:** Contar identificadores año-correlativo por cohorte y sus registros asociados.

**Explicación:** No suma identidades de años distintos como si fueran personas globales. Promedio calculado por aspirante de cohorte.

**Código ejecutable:**

```python
pipeline = [{'$group': {'_id': {'anio': '$anio_ingreso', 'cohorte': '$aspirante.cohorte_id'},
             'registros': {'$sum': 1}}},
 {'$group': {'_id': '$_id.anio',
             'aspirantes_cohorte': {'$sum': 1},
             'registros': {'$sum': '$registros'},
             'minimo_registros': {'$min': '$registros'},
             'maximo_registros': {'$max': '$registros'},
             'promedio_registros': {'$avg': '$registros'}}},
 {'$project': {'_id': 0,
               'anio': '$_id',
               'aspirantes_cohorte': 1,
               'registros': 1,
               'minimo_registros': 1,
               'maximo_registros': 1,
               'promedio_registros': {'$round': ['$promedio_registros', 2]}}},
 {'$sort': {'anio': 1}}]
with timeout(60):
    resultado = list(coleccion.aggregate(
        pipeline, maxTimeMS=60000, allowDiskUse=False))
print(resultado)
```

**Verificación:** correcta; 0.2987 segundos. Se devolvieron 10 filas. Resultado completo:

```json
[
  {
    "aspirantes_cohorte": 6148,
    "registros": 20277,
    "minimo_registros": 1,
    "maximo_registros": 8,
    "anio": 2015,
    "promedio_registros": 3.3
  },
  {
    "aspirantes_cohorte": 6428,
    "registros": 22137,
    "minimo_registros": 1,
    "maximo_registros": 12,
    "anio": 2016,
    "promedio_registros": 3.44
  },
  {
    "aspirantes_cohorte": 5976,
    "registros": 21581,
    "minimo_registros": 1,
    "maximo_registros": 12,
    "anio": 2017,
    "promedio_registros": 3.61
  },
  {
    "aspirantes_cohorte": 5738,
    "registros": 20871,
    "minimo_registros": 1,
    "maximo_registros": 16,
    "anio": 2018,
    "promedio_registros": 3.64
  },
  {
    "aspirantes_cohorte": 5310,
    "registros": 17865,
    "minimo_registros": 1,
    "maximo_registros": 9,
    "anio": 2019,
    "promedio_registros": 3.36
  },
  {
    "aspirantes_cohorte": 4997,
    "registros": 17931,
    "minimo_registros": 1,
    "maximo_registros": 13,
    "anio": 2020,
    "promedio_registros": 3.59
  },
  {
    "aspirantes_cohorte": 6861,
    "registros": 30644,
    "minimo_registros": 1,
    "maximo_registros": 8,
    "anio": 2021,
    "promedio_registros": 4.47
  },
  {
    "aspirantes_cohorte": 6380,
    "registros": 24237,
    "minimo_registros": 1,
    "maximo_registros": 10,
    "anio": 2022,
    "promedio_registros": 3.8
  },
  {
    "aspirantes_cohorte": 4638,
    "registros": 19047,
    "minimo_registros": 1,
    "maximo_registros": 10,
    "anio": 2023,
    "promedio_registros": 4.11
  },
  {
    "aspirantes_cohorte": 3861,
    "registros": 13863,
    "minimo_registros": 1,
    "maximo_registros": 10,
    "anio": 2024,
    "promedio_registros": 3.59
  }
]
```

## 26. Histograma de registros por aspirante de cohorte

**Objetivo:** Determinar cuántas cohortes individuales tienen uno, dos o más registros.

**Explicación:** La cantidad es de registros publicados, no intentos inferidos; incluye repeticiones originales.

**Código ejecutable:**

```python
pipeline = [{'$group': {'_id': '$aspirante.cohorte_id', 'registros': {'$sum': 1}}},
 {'$group': {'_id': '$registros', 'aspirantes_cohorte': {'$sum': 1}}},
 {'$project': {'_id': 0, 'registros_por_aspirante': '$_id', 'aspirantes_cohorte': 1}},
 {'$sort': {'registros_por_aspirante': 1}}]
with timeout(60):
    resultado = list(coleccion.aggregate(
        pipeline, maxTimeMS=60000, allowDiskUse=False))
print(resultado)
```

**Verificación:** correcta; 0.1936 segundos. Se devolvieron 15 filas. Extracto de las primeras 3 filas; no es el total:

```json
[
  {
    "aspirantes_cohorte": 3603,
    "registros_por_aspirante": 1
  },
  {
    "aspirantes_cohorte": 18471,
    "registros_por_aspirante": 2
  },
  {
    "aspirantes_cohorte": 5681,
    "registros_por_aspirante": 3
  }
]
```

## 27. Aprobación en ambas materias dentro de la cohorte

**Objetivo:** Consultar hasta cien aspirantes de 2024 con ambas materias aprobadas.

**Explicación:** Reutiliza both_subjects, devuelve truncado si hay más. La lista acotada no es un total ni demuestra admisión definitiva.

**Código ejecutable:**

```python
with timeout(60):
    filas, truncado = consultas.both_subjects(conexiones, BothFilters(**{'anio': 2024, 'limite': 100}))
resultado = {"registros": filas, "truncado": truncado, "limite": 100}
print(resultado)
```

**Verificación:** correcta; 0.0275 segundos. Se devolvieron 100 filas limitadas. Metadatos y extracto de las primeras 3:

```json
{
  "truncado": true,
  "limite": 100,
  "filas_devueltas": 100,
  "extracto_primeras_3": [
    {
      "aspirante_cohorte": "2024:006e14a54c4e91332fa4f",
      "materias": [
        "COMPUTACION",
        "MATEMATICA"
      ]
    },
    {
      "aspirante_cohorte": "2024:00d7ed673f478f6a7a2b",
      "materias": [
        "COMPUTACION",
        "MATEMATICA"
      ]
    },
    {
      "aspirante_cohorte": "2024:00dcbc3eeef21db0d63c",
      "materias": [
        "COMPUTACION",
        "MATEMATICA"
      ]
    }
  ]
}
```

## 28. Múltiples carreras informadas dentro del año

**Objetivo:** Contar aspirantes de cohorte con más de una categoría de carrera observada.

**Explicación:** El conjunto usa valor y estado, excluye carrera ausente y no sigue a personas entre años. No infiere el orden de cambios.

**Código ejecutable:**

```python
pipeline = [{'$match': {'carrera.valor': {'$ne': None}}},
 {'$group': {'_id': {'anio': '$anio_ingreso', 'cohorte': '$aspirante.cohorte_id'},
             'carreras': {'$addToSet': {'valor': '$carrera.valor',
                                        'estado': '$carrera.estado_normalizacion'}}}},
 {'$project': {'anio': '$_id.anio', 'cantidad_carreras': {'$size': '$carreras'}}},
 {'$match': {'cantidad_carreras': {'$gt': 1}}},
 {'$group': {'_id': '$anio',
             'aspirantes_con_multiples_carreras': {'$sum': 1},
             'maximo_categorias_observadas': {'$max': '$cantidad_carreras'}}},
 {'$project': {'_id': 0,
               'anio': '$_id',
               'aspirantes_con_multiples_carreras': 1,
               'maximo_categorias_observadas': 1}},
 {'$sort': {'anio': 1}}]
with timeout(60):
    resultado = list(coleccion.aggregate(
        pipeline, maxTimeMS=60000, allowDiskUse=False))
print(resultado)
```

**Verificación:** correcta; 1.0076 segundos. Se devolvieron 9 filas. Resultado completo:

```json
[
  {
    "aspirantes_con_multiples_carreras": 727,
    "maximo_categorias_observadas": 4,
    "anio": 2016
  },
  {
    "aspirantes_con_multiples_carreras": 570,
    "maximo_categorias_observadas": 4,
    "anio": 2017
  },
  {
    "aspirantes_con_multiples_carreras": 549,
    "maximo_categorias_observadas": 3,
    "anio": 2018
  },
  {
    "aspirantes_con_multiples_carreras": 483,
    "maximo_categorias_observadas": 4,
    "anio": 2019
  },
  {
    "aspirantes_con_multiples_carreras": 456,
    "maximo_categorias_observadas": 4,
    "anio": 2020
  },
  {
    "aspirantes_con_multiples_carreras": 1866,
    "maximo_categorias_observadas": 4,
    "anio": 2021
  },
  {
    "aspirantes_con_multiples_carreras": 427,
    "maximo_categorias_observadas": 3,
    "anio": 2022
  },
  {
    "aspirantes_con_multiples_carreras": 306,
    "maximo_categorias_observadas": 4,
    "anio": 2023
  },
  {
    "aspirantes_con_multiples_carreras": 235,
    "maximo_categorias_observadas": 3,
    "anio": 2024
  }
]
```

## 29. Coexistencia de resultados por cohorte y materia

**Objetivo:** Contar aspirantes con registros aprobados y no aprobados de la misma materia dentro del año.

**Explicación:** No presupone mejoría, secuencia de intentos ni fecha real de examen. Solo constata coexistencia de resultados publicados.

**Código ejecutable:**

```python
pipeline = [{'$group': {'_id': {'anio': '$anio_ingreso',
                     'cohorte': '$aspirante.cohorte_id',
                     'materia': '$materia'},
             'resultados': {'$addToSet': '$aprobado'}}},
 {'$match': {'resultados': {'$all': [True, False]}}},
 {'$group': {'_id': {'anio': '$_id.anio', 'materia': '$_id.materia'},
             'aspirantes_con_ambos_resultados': {'$sum': 1}}},
 {'$project': {'_id': 0,
               'anio': '$_id.anio',
               'materia': '$_id.materia',
               'aspirantes_con_ambos_resultados': 1}},
 {'$sort': {'anio': 1, 'materia': 1}}]
with timeout(60):
    resultado = list(coleccion.aggregate(
        pipeline, maxTimeMS=60000, allowDiskUse=False))
print(resultado)
```

**Verificación:** correcta; 1.0579 segundos. Se devolvieron 20 filas. Extracto de las primeras 3 filas; no es el total:

```json
[
  {
    "aspirantes_con_ambos_resultados": 1084,
    "anio": 2015,
    "materia": "COMPUTACION"
  },
  {
    "aspirantes_con_ambos_resultados": 947,
    "anio": 2015,
    "materia": "MATEMATICA"
  },
  {
    "aspirantes_con_ambos_resultados": 1147,
    "anio": 2016,
    "materia": "COMPUTACION"
  }
]
```

## 30. Catálogos reales con estado de carrera

**Objetivo:** Consultar los dominios observados para filtros y análisis.

**Explicación:** Reutiliza catalogs: $facet para años, materias y tipos, más careers compartida para categorías de carrera. No se considera otra consulta nueva por cada opción del catálogo.

**Código ejecutable:**

```python
with timeout(60):
    resultado = consultas.catalogs(conexiones)
print(resultado)
```

**Verificación:** correcta; 0.7656 segundos. Resumen de dominios y extracto de carreras (catálogo completo en el reporte):

```json
{
  "anios": [
    2015,
    2016,
    2017,
    2018,
    2019,
    2020,
    2021,
    2022,
    2023,
    2024
  ],
  "materias": [
    "COMPUTACION",
    "MATEMATICA",
    "MATEMATICA ITUGS"
  ],
  "tipos_institucion": [
    "MUNICIPAL",
    "POR COOPERATIVA",
    "PRIVADO",
    "PUBLICO"
  ],
  "categorias_carrera": 16,
  "extracto_carreras_primeras_3": [
    {
      "id": "carrera:f6070b5a4c2b69c14d4d6bb9325c7475967423ab2ac73530d51585aa97da8bfb",
      "carrera": "INGENIERIA EN CIENCIAS Y SISTEMAS",
      "estado": "completa",
      "registros": 42427,
      "aprobados": 6533
    },
    {
      "id": "carrera:dbfd9b3c47260f28f1ff1eb65a11c88dc1f9d94bb4ed2f1204e6314a7d2009b9",
      "carrera": "INGENIERIA INDUSTRIAL",
      "estado": "completa",
      "registros": 28704,
      "aprobados": 3458
    },
    {
      "id": "carrera:b986db06a72c36cf432e23d63db9c9ed4424c4822514b66ab6402cd02e39d6f8",
      "carrera": "INGENIERIA CIVIL",
      "estado": "completa",
      "registros": 27638,
      "aprobados": 3174
    }
  ]
}
```

## Conservación de las consultas Neo4j

Los seis archivos Cypher existentes en [consultas/neo4j](../consultas/neo4j) se
conservan sin cambios. Su modelo y resultados históricos están en [etapa 4](etapa-4.md).

| Archivo | Objetivo |
| --- | --- |
| 01_aprobacion.cypher | Tasa por año y materia |
| 02_carreras.cypher | Resultados por carrera y materia |
| 03_visualizacion.cypher | Caminos de aspirantes, evaluaciones, materias y carreras |
| 04_aspirante.cypher | Registros de un aspirante dentro de su cohorte |
| 05_ambas_materias.cypher | Aprobación informada en Matemática y Computación |
| 06_procedencia.cypher | Procedencia educativa por departamento y tipo |

Estos archivos no se vuelven a contar como MongoDB. Las equivalencias analíticas
reutilizadas no cambian la fuente de los endpoints existentes: estadísticas MongoDB,
grafos Neo4j. La presente ejecución de 30 consultas no carga ni modifica el grafo.

## Pruebas y requisitos restantes

```bash
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p test_mongodb_queries.py -v
USAC_RUN_DB_TESTS=1 PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -v
npm test --prefix frontend
npm run build --prefix frontend
npm run test:e2e --prefix frontend
git diff --check
```

Ejecutar de forma secuencial. Las pruebas del catálogo cubren 30 ids, reutilización
de siete funciones, destino fijo, límites, lectura exclusiva y detección de totales
inconsistentes. Las verificaciones reales de este documento se obtienen al ejecutar
las consultas, no sustituyendo sus resultados con mocks.

Los registros representan ocurrencias publicadas, incluidas repeticiones. Sexo y
nacimiento ausentes no se imputan. Carrera incluye estado completo/recortado/ausente.
Aspirante significa año+correlativo, sin identidad global. Edad es aproximada y la
procedencia no representa residencia. Las consultas no demuestran causalidad ni
admisión definitiva.

El requisito de al menos 20 consultas queda cubierto por el catálogo de 30.
La colección materializada resumen_carrera sigue sin implementarse; no se crea
como efecto de estas consultas de lectura. No hay commits, merges ni push en esta etapa.

## Cierre de la verificación de esta etapa

Se ejecutaron secuencialmente 46 pruebas backend (incluyen siete pruebas unitarias
nuevas y una integración que ejecuta las 30 consultas reales), 13 pruebas frontend,
compilación Vite y 8 recorridos Chrome: todas correctas. También pasaron pip check,
validación de Compose y git diff --check. No se cambiaron React, FastAPI, ETL,
proyector ni los seis archivos Cypher. Los conteos de integración permanecieron
en 208453 documentos MongoDB, 265293 nodos y 1222881 relaciones Neo4j.

Resultados destacados verificados: 56337 aspirantes de cohorte en la consulta 25;
189002 registros con nacimiento conocido en 19; 188998 edades aproximadas dentro
del rango declarado en 20; 28010 registros con carrera recortada en 23; 805 grupos
repetidos y 834 ocurrencias adicionales en 24. La consulta 13 tiene 450 grupos
porque conserva también ausencias y precisión; no debe compararse directamente
con los 448 nodos LocalidadEducativa, que omiten datos nulos. La consulta 27 devuelve
100 registros con truncado=true: es una lista limitada, no el número total de
aspirantes que aprobaron ambas materias.


## Ejecución desde React

La sección **Consultas NoSQL**, ruta /consultas, permite seleccionar y ejecutar
las 30 entradas de este documento; ninguna queda solo documentada. La pestaña
Neo4j también ejecuta los seis archivos Cypher originales, con tabla y grafo cuando
corresponde. Se reutiliza el catálogo sin reconstruir ni borrar consultas.
Ver [integración, límites y seguridad](explorador-consultas.md). No se admiten
pipelines ni texto Cypher arbitrario desde el navegador.
