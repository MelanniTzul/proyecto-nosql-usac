MATCH p = (a:AspiranteCohorte)-[:TIENE_REGISTRO]->(e:Evaluacion:USACAdmision)-[:DE_MATERIA]->(m:Materia)
MATCH q = (e)-[:ASPIRA_A]->(r:CarreraObservada)
WHERE e.anio_ingreso = $anio AND m.nombre = $materia
  AND r.id = $carrera_id AND e.aprobado = $aprobado
RETURN p, q LIMIT 100;
