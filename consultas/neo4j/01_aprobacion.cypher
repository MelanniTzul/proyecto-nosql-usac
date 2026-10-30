MATCH (e:Evaluacion:USACAdmision)-[:EN_COHORTE]->(c:Cohorte)
MATCH (e)-[:DE_MATERIA]->(m:Materia)
WHERE c.anio >= $desde AND c.anio <= $hasta
WITH c.anio AS anio, m.nombre AS materia, count(e) AS registros,
     sum(CASE WHEN e.aprobado THEN 1 ELSE 0 END) AS aprobados
RETURN anio, materia, registros, aprobados,
       round(100.0 * aprobados / registros, 2) AS porcentaje
ORDER BY anio, materia;
