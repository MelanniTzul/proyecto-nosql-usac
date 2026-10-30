import { useState } from 'react';
import useApi from '../hooks/useApi';
import useFilters from '../hooks/useFilters';
import { endpoint } from '../services/api';
import FilterBar from '../components/filters/FilterBar';
import { PageHeading, QueryState, EmptyState, SourceNote } from '../components/common/States';
import { number, resultName } from '../utils/format';

export default function EvaluationsPage() {
  const [filters, apply, reset] = useFilters({ anio: '', materia: '', aprobado: '', limite: '25' });
  const signature = JSON.stringify(filters);
  const [history, setHistory] = useState({ key: signature, index: 0, cursors: [null] });
  const page = history.key === signature ? history : { key: signature, index: 0, cursors: [null] };
  const query = useApi(endpoint('evaluaciones', { ...filters, cursor: page.cursors[page.index] }));
  const [selected, setSelected] = useState(null);
  const active = selected?.key === signature ? selected.data : null;
  function move(index, next = null) {
    const cursors = [...page.cursors];
    if (next) cursors[index] = next;
    setHistory({ key: signature, index, cursors }); setSelected(null);
  }
  return <><PageHeading eyebrow="CONSULTA DE REGISTROS" title="Evaluaciones" description="Consulta registros de la fuente y revisa sus advertencias de calidad."/>
    <FilterBar values={filters} fields={['anio', 'materia', 'aprobado']} onApply={apply} onReset={reset}/>
    <section className="panel evaluation-panel"><div className="panel-heading"><div><h2>Registros de evaluación</h2><p>Registros ordenados por identificador</p></div><label className="page-size">Por página<select value={filters.limite} onChange={(e) => apply({ ...filters, limite: e.target.value })}>{[25,50,100].map((n) => <option key={n} value={n}>{n}</option>)}</select></label></div>
    <QueryState query={query}>{(rows, meta) => rows.length ? <><div className="table-scroll"><table aria-label="Evaluaciones de admisión"><thead><tr>{['Año', 'Materia', 'Convocatoria', 'Resultado', 'Carrera observada', 'Calidad', 'Detalle'].map((name) => <th key={name}>{name}</th>)}</tr></thead><tbody>{rows.map((row) => <tr key={row.id}><td>{row.anio_ingreso}</td><td className="subject-cell">{row.materia}</td><td>{row.numero_fecha_evaluacion}</td><td><span className={`badge ${row.aprobado ? 'success' : 'neutral'}`}>{resultName(row.aprobado)}</span></td><td className="career-cell">{row.carrera.valor || 'Sin información'}{row.carrera.estado_normalizacion === 'recortada' && <span className="sub-label">Texto recortado en la fuente</span>}</td><td>{row.advertencias.length ? <span className="badge warning">{row.advertencias.length} advertencias</span> : <span className="muted">Sin advertencias</span>}</td><td><button className="text-button" onClick={() => setSelected({ key: signature, data: row })} aria-label={`Ver detalle de evaluación ${row.id}`}>Ver ↗</button></td></tr>)}</tbody></table></div><div className="pagination"><span>{number(rows.length)} registros · página {page.index + 1}</span><div><button className="button secondary" disabled={page.index === 0} onClick={() => move(page.index - 1)}>← Anterior</button><button className="button secondary" disabled={!meta.siguiente_cursor} onClick={() => move(page.index + 1, meta.siguiente_cursor)}>Siguiente →</button></div></div></> : <EmptyState clear={reset}/>}</QueryState></section>
    {active && <section className="panel record-detail" aria-label="Detalle de evaluación"><div className="panel-heading"><h2>Detalle del registro</h2><button className="text-button" onClick={() => setSelected(null)}>Cerrar</button></div><dl className="property-list"><dt>Identificador</dt><dd>{active.id}</dd><dt>Aspirante de cohorte</dt><dd>{active.aspirante.cohorte_id}</dd><dt>Fecha de asignación</dt><dd>{active.fecha_asignacion}</dd><dt>Departamento educativo</dt><dd>{active.procedencia_educativa.departamento || 'Sin información'}</dd><dt>Municipio observado</dt><dd>{active.procedencia_educativa.municipio || 'Sin información'}</dd><dt>Tipo educativo</dt><dd>{active.procedencia_educativa.tipo || 'Sin información'}</dd></dl><h3>Advertencias de la fuente</h3>{active.advertencias.length ? <ul className="warning-list">{active.advertencias.map((a) => <li key={a}>{a}</li>)}</ul> : <p>No se registraron advertencias.</p>}<p className="method-note">La convocatoria no equivale a un número de intento. El correlativo solo se agrupa dentro de su año.</p></section>}
    <SourceNote/>
  </>;
}
