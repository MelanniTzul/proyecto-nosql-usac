import { lazy, Suspense, useState } from 'react';
import useApi from '../hooks/useApi';
import useFilters from '../hooks/useFilters';
import { endpoint } from '../services/api';
import FilterBar from '../components/filters/FilterBar';
import { Loading, PageHeading, QueryState, EmptyState, SourceNote } from '../components/common/States';
const GraphCanvas = lazy(() => import('../components/graph/GraphCanvas'));
const types = { Evaluacion: 'Evaluación', AspiranteCohorte: 'Aspirante de cohorte', Cohorte: 'Año de ingreso', Materia: 'Materia', CarreraObservada: 'Carrera observada', LocalidadEducativa: 'Localidad educativa', Departamento: 'Departamento', TipoInstitucion: 'Tipo de institución' };
const colors = ['#08275C','#25A744','#123B69','#5e82ab','#355c89','#7894b3','#9eb2ca','#687b93'];

export function GraphView({ data, meta, onCohort, canReturn, onReturn }) {
  const [selectedId, setSelectedId] = useState(null);
  const selected = data.nodes.find((n) => n.id === selectedId);
  return <><div className="graph-summary"><div><strong>{data.nodes.filter((n) => n.tipo === 'Evaluacion').length} evaluaciones</strong><span>{data.nodes.length} nodos · {data.edges.length} relaciones</span></div>{canReturn && <button className="button secondary" onClick={onReturn}>← Volver a filtros</button>}</div>
    {meta.truncado && <p className="info-note">Subgrafo parcial: se alcanzó el límite de la consulta. Ajusta los filtros para explorar otros registros; esta selección no es una muestra estadística.</p>}
    <div className="graph-layout"><div className="graph-main"><Suspense fallback={<Loading label="Preparando visualización…"/>}><GraphCanvas data={data} onSelect={(node) => setSelectedId(node.id)}/></Suspense><div className="graph-legend">{Object.keys(types).filter((type) => data.nodes.some((n) => n.tipo === type)).map((type) => <span key={type}><i style={{ backgroundColor: colors[Object.keys(types).indexOf(type)] }}/>{types[type]}</span>)}</div></div>
    <aside className="node-panel" aria-label="Propiedades del nodo seleccionado"><p className="eyebrow">INSPECTOR DE NODOS</p>{selected ? <><h2>{types[selected.tipo]}</h2><dl className="property-list">{Object.entries(selected.properties).map(([key, value]) => <div key={key}><dt>{key.replaceAll('_', ' ')}</dt><dd>{value === null ? 'Sin información' : Array.isArray(value) ? value.join(' · ') || 'Sin advertencias' : String(value)}</dd></div>)}</dl>{selected.tipo === 'AspiranteCohorte' && <button className="button" onClick={() => onCohort(selected.properties.id)}>Consultar esta cohorte ↗</button>}</> : <div className="inspector-empty"><span>◇</span><h3>Explora una conexión</h3><p>Selecciona un nodo en el grafo o en la lista accesible para ver sus propiedades.</p></div>}</aside></div>
    <details className="data-details graph-accessible"><summary>Lista accesible de nodos y relaciones</summary><div className="node-list">{data.nodes.map((node) => <button className={`node-list-item ${selectedId === node.id ? 'selected' : ''}`} key={node.id} onClick={() => setSelectedId(node.id)}>{types[node.tipo]} · {node.properties.nombre || node.properties.nombre_observado || node.properties.id}</button>)}</div><ul className="edge-list">{data.edges.map((edge) => <li key={edge.id}>{edge.source} → <strong>{edge.tipo}</strong> → {edge.target}</li>)}</ul></details>
  </>;
}
export default function GraphPage() {
  const [filters, apply, reset] = useFilters({ anio: '2024', materia: '', aprobado: '', carrera_id: '', limite: '25' });
  const [focus, setFocus] = useState(null);
  const key = JSON.stringify(filters);
  const cohort = focus?.key === key ? focus.id : null;
  const url = cohort ? endpoint(`grafo/aspirantes/${encodeURIComponent(cohort)}`, { limite: filters.limite }) : filters.anio ? endpoint('grafo', filters) : null;
  const query = useApi(url);
  return <><PageHeading eyebrow="EXPLORACIÓN DE RELACIONES" title="Descubre las relaciones" description="Un recorrido por el contexto de las evaluaciones, sin unir identidades entre años."/>
    <FilterBar values={filters} fields={['anio', 'materia', 'aprobado', 'carrera_id', 'limite']} requiredFields={['anio']} onApply={(next) => { setFocus(null); apply(next); }} onReset={() => { setFocus(null); reset(); }}/>
    {cohort && <p className="info-note">Vista del aspirante de cohorte {cohort}. Se muestran sus registros del año; los filtros de materia, resultado y carrera no se aplican en esta vista.</p>}
    {!filters.anio && <p className="info-note">Selecciona un año para consultar un subgrafo.</p>}
    <section className="panel graph-panel"><QueryState query={query}>{(data, meta) => data.nodes.length ? <GraphView key={url} data={data} meta={meta} onCohort={(id) => setFocus({ key, id })} canReturn={Boolean(cohort)} onReturn={() => setFocus(null)}/> : <EmptyState clear={reset} message="No hay conexiones para los filtros seleccionados."/>}</QueryState></section><SourceNote/><p className="method-note">Aspirante de cohorte = año + correlativo. La procedencia corresponde a la institución educativa, no a la residencia.</p>
  </>;
}
