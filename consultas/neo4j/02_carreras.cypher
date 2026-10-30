MATCH (e:Evaluacion:USACAdmision)-[:ASPIRA_A]->(r:CarreraObservada)
MATCH (e)-[:DE_MATERIA]->(m:Materia)
WHERE e.anio_ingreso = $anio AND m.nombre = $materia
RETURN r.nombre AS carrera, r.estado_normalizacion AS estado,
       count(e) AS registros,
       sum(CASE WHEN e.aprobado THEN 1 ELSE 0 END) AS aprobados
ORDER BY registros DESC;
