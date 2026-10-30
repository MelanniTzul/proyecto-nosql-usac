MATCH p = (a:AspiranteCohorte:USACAdmision {id: $cohorte_id})-[:TIENE_REGISTRO]->(e:Evaluacion)-[:DE_MATERIA]->(m:Materia)
RETURN p ORDER BY e.convocatoria, e.fecha_asignacion, e.id;
