MATCH (e:Evaluacion:USACAdmision)-[:PROCEDENCIA_EDUCATIVA]->(l:LocalidadEducativa)-[:EN_DEPARTAMENTO]->(d:Departamento)
MATCH (e)-[:TIPO_INSTITUCION]->(t:TipoInstitucion)
WHERE e.anio_ingreso = $anio
RETURN d.nombre AS departamento, t.nombre AS tipo, count(e) AS registros,
       sum(CASE WHEN e.aprobado THEN 1 ELSE 0 END) AS aprobados
ORDER BY registros DESC;
