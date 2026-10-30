import useApi from '../hooks/useApi';
import useFilters from '../hooks/useFilters';
import { endpoint } from '../services/api';
import FilterBar from '../components/filters/FilterBar';
import { PageHeading, QueryState, EmptyState, SourceNote } from '../components/common/States';
import { ChartPanel, TrendChart, ComparisonChart, DataTable } from '../components/charts/Charts';
import { number, percent, careerName } from '../utils/format';

function CareerSection() {
  const [f, apply, reset] = useFilters({ anio: '2024', materia: '' }, 'carrera_');
  const query = useApi(f.anio ? endpoint('resultados/carreras', f) : null);
  return <ChartPanel title="Resultados por carrera" subtitle="El nombre completo y el texto recortado son categorías distintas"><FilterBar values={f} fields={['anio', 'materia']} requiredFields={['anio']} onApply={apply} onReset={reset}/>{!f.anio && <p className="info-note">Selecciona un año para consultar carreras.</p>}<QueryState query={query}>{(rows) => rows.length ? <><ComparisonChart rows={rows.map((r) => ({ ...r, nombre: careerName(r) }))}/><DataTable label="Resultados por carrera" headers={['Carrera observada', 'Estado', 'Evaluaciones', 'Aprobadas']} rows={rows.map((r) => [r.carrera || 'Sin información', r.estado, number(r.registros), number(r.aprobados)])}/></> : <EmptyState clear={reset}/>}</QueryState></ChartPanel>;
}
function ProvenanceSection() {
  const [f, apply, reset] = useFilters({ anio: '2024' }, 'procedencia_');
  const query = useApi(f.anio ? endpoint('procedencia', f) : null);
  return <ChartPanel title="Procedencia educativa" subtitle="Ubicación y tipo de institución; no residencia del aspirante"><FilterBar values={f} fields={['anio']} requiredFields={['anio']} onApply={apply} onReset={reset}/>{!f.anio && <p className="info-note">Selecciona un año para consultar procedencia.</p>}<QueryState query={query}>{(rows) => {
    const groups = new Map();
    for (const r of rows) { const name = r.departamento || 'Sin información'; const item = groups.get(name) || { nombre: name, registros: 0, aprobados: 0 }; item.registros += r.registros; item.aprobados += r.aprobados; groups.set(name, item); }
    const plotted = [...groups.values()].sort((a, b) => b.registros - a.registros).slice(0, 10);
    return rows.length ? <><ComparisonChart rows={plotted}/><p className="chart-footnote">Diez departamentos con más registros. La tabla incluye todos los departamentos y tipos.</p><details className="data-details"><summary>Ver tabla completa de procedencia</summary><DataTable label="Procedencia educativa" headers={['Departamento', 'Tipo', 'Evaluaciones', 'Aprobadas']} rows={rows.map((r) => [r.departamento || 'Sin información', r.tipo || 'Sin información', number(r.registros), number(r.aprobados)])}/></details></> : <EmptyState clear={reset}/>;
  }}</QueryState></ChartPanel>;
}
export default function StatisticsPage() {
  // Secciones independientes: no se propagan filtros que un endpoint no admite.
  const [range, apply, reset] = useFilters({ desde: '2015', hasta: '2024' }, 'historico_');
  const query = useApi(range.desde && range.hasta ? endpoint('estadisticas/aprobacion', range) : null);
  return <><PageHeading eyebrow="ESTADÍSTICAS" title="Resultados en perspectiva" description="Compara cohortes y categorías con filtros propios para cada análisis."/>
    <ChartPanel title="Aprobación por año y materia" subtitle="Porcentaje calculado a partir de los registros de cada grupo"><FilterBar values={range} fields={['desde', 'hasta']} requiredFields={['desde', 'hasta']} onApply={apply} onReset={reset}/><QueryState query={query}>{(rows) => rows.length ? <><TrendChart rows={rows}/><details className="data-details"><summary>Ver tabla histórica</summary><DataTable label="Estadísticas históricas" headers={['Año', 'Materia', 'Registros', 'Aprobación']} rows={rows.map((r) => [r.anio, r.materia, number(r.registros), percent(r.porcentaje)])}/></details></> : <EmptyState clear={reset}/>}</QueryState></ChartPanel>
    <div className="statistics-sections"><CareerSection/><ProvenanceSection/></div><SourceNote/>
  </>;
}
