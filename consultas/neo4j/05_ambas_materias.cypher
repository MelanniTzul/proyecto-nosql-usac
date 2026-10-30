MATCH (a:AspiranteCohorte:USACAdmision)-[:TIENE_REGISTRO]->(e:Evaluacion)-[:DE_MATERIA]->(m:Materia)
WHERE a.anio_ingreso = $anio AND e.aprobado = true
  AND m.nombre IN ['MATEMATICA', 'COMPUTACION']
WITH a, collect(DISTINCT m.nombre) AS materias
WHERE size(materias) = 2
RETURN a.id AS aspirante_cohorte, materias ORDER BY aspirante_cohorte LIMIT 100;
