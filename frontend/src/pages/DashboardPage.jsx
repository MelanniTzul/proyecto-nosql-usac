import { Link } from 'react-router';
import useApi from '../hooks/useApi';
import useFilters from '../hooks/useFilters';
import { endpoint } from '../services/api';
import { PageHeading, QueryState, EmptyState, SourceNote } from '../components/common/States';
import StatCards from '../components/common/StatCards';
import FilterBar from '../components/filters/FilterBar';
import { ChartPanel, ResultChart, TrendChart, DataTable } from '../components/charts/Charts';
import { number, percent } from '../utils/format';

export default function DashboardPage() {
  const [filters, apply, reset] = useFilters({ anio: '', materia: '', aprobado: '' });
  const stats = useApi(endpoint('estadisticas', filters));
  const trend = useApi(endpoint('estadisticas/aprobacion'));
  return <><PageHeading eyebrow="UNA MIRADA A LOS DATOS" title="Panorama de admisión" description="Explora los resultados de las pruebas específicas de Ingeniería USAC."><span className="period-pill">2015 — 2024 <span>Datos disponibles</span></span></PageHeading>
    <FilterBar values={filters} fields={['anio', 'materia', 'aprobado']} onApply={apply} onReset={reset}/>
    <QueryState query={stats}>{(data) => <><StatCards data={data}/>{filters.aprobado !== '' && <p className="info-note">Los indicadores incluyen únicamente el resultado seleccionado; su porcentaje usa ese subconjunto como denominador.</p>}
      <div className="dashboard-charts"><ChartPanel title="Evolución de la aprobación" subtitle="Serie histórica 2015–2024 · todas las materias y resultados"><QueryState query={trend}>{(rows) => rows.length ? <><TrendChart rows={rows}/><details className="data-details"><summary>Ver tabla de datos</summary><DataTable label="Aprobación histórica" headers={['Año', 'Materia', 'Evaluaciones', 'Aprobación']} rows={rows.map((r) => [r.anio, r.materia, number(r.registros), percent(r.porcentaje)])}/></details></> : <EmptyState/>}</QueryState></ChartPanel>
      <ChartPanel title="Distribución de resultados" subtitle="Corresponde a los filtros de los indicadores">{data.registros ? <ResultChart data={data}/> : <EmptyState clear={reset}/>}</ChartPanel></div>
      <div className="bottom-grid"><section className="panel quality-panel"><p className="eyebrow">CALIDAD Y CONTEXTO</p><h2>Interpretar con transparencia</h2><p><strong>{number(data.registros_con_advertencias)}</strong> registros de esta selección contienen advertencias de calidad. Los valores recortados y ausentes se conservan sin reconstruir información.</p><Link to="/evaluaciones" className="inline-link">Consultar evaluaciones <span>↗</span></Link></section><section className="graph-promo"><span className="eyebrow">EXPLORA LAS CONEXIONES</span><h2>Cada registro tiene un contexto.</h2><p>Descubre las relaciones entre evaluaciones, materias, carreras y procedencia educativa.</p><Link to="/grafo" className="light-link">Abrir explorador de grafos <span>↗</span></Link><span className="promo-orbit" aria-hidden="true">◇</span></section></div>
    </>}</QueryState><SourceNote/><p className="method-note">Una evaluación es un registro publicado, no una persona única. La serie histórica tiene su propio alcance y no cambia con los filtros de los indicadores.</p></>;
}
