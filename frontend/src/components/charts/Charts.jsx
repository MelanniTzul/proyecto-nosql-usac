import { ResponsiveContainer, BarChart, Bar, Cell, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { number, percent } from '../../utils/format';
const subjectColors = { COMPUTACION: '#0B2D66', MATEMATICA: '#2785C4', 'MATEMATICA ITUGS': '#159447' };
const subjectStyles = {
  COMPUTACION: { dash: undefined, marker: 'circle' },
  MATEMATICA: { dash: '7 4', marker: 'square' },
  'MATEMATICA ITUGS': { dash: '2 3', marker: 'triangle' },
};

function SubjectMarker({ cx, cy, value = 0, subject, active = false }) {
  if (!Number.isFinite(cx) || !Number.isFinite(cy) || value === null) return null;
  const size = active ? 5 : 4;
  const shared = { fill: subjectColors[subject] || '#0B2D66', stroke: '#FFFFFF', strokeWidth: 1 };
  const marker = subjectStyles[subject]?.marker;
  if (marker === 'square') return <rect x={cx - size} y={cy - size} width={size * 2} height={size * 2} {...shared}/>;
  if (marker === 'triangle') return <path d={`M${cx},${cy - size - 1} L${cx + size + 1},${cy + size} L${cx - size - 1},${cy + size} Z`} {...shared}/>;
  return <circle cx={cx} cy={cy} r={size} {...shared}/>;
}

function SubjectLegend({ payload = [] }) {
  return <ul style={{ display: 'flex', justifyContent: 'center', flexWrap: 'wrap', gap: '6px 12px', margin: 0, padding: 0, listStyle: 'none', fontSize: 11, color: '#24354b' }}>{payload.map((item) => <li key={item.value} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
    <svg width="32" height="16" aria-hidden="true"><line x1="1" x2="31" y1="8" y2="8" stroke={subjectColors[item.value]} strokeWidth="3" strokeDasharray={subjectStyles[item.value]?.dash}/><SubjectMarker cx={16} cy={8} subject={item.value}/></svg>
    <span>{item.value}</span>
  </li>)}</ul>;
}

const resultColors = { aprobados: '#159447', no_aprobados: '#AAB8C9' };
const legendLabel = (value) => <span style={{ color: '#24354b' }}>{value}</span>;

function ChartTooltip({ active, payload, label, formatValue = number }) {
  if (!active || !payload?.length) return null;
  return <div className="recharts-default-tooltip" style={{ background: '#FFFFFF', border: '1px solid #d5deeb', padding: '10px 12px', color: '#24354b' }}>
    <p style={{ marginBottom: 6 }}>{label}</p>
    <ul style={{ margin: 0, padding: 0, listStyle: 'none' }}>{payload.map((item) => <li key={item.dataKey} style={{ display: 'flex', alignItems: 'center', gap: 7, padding: '3px 0' }}>
      <span aria-hidden="true" style={{ width: 9, height: 9, borderRadius: 2, background: item.payload.color || item.color, flexShrink: 0 }}/>
      <span>{item.dataKey === 'registros' ? item.payload.nombre : item.name}: {formatValue(item.value)}</span>
    </li>)}</ul>
  </div>;
}

export function ChartPanel({ title, subtitle, children, table, className = '' }) {
  return <section className={`panel ${className}`}><div className="panel-heading"><div><h2>{title}</h2><p>{subtitle}</p></div><span className="panel-mark" aria-hidden="true">↗</span></div>{children}{table && <details className="data-details"><summary>Ver tabla de datos</summary>{table}</details>}</section>;
}

export function ResultChart({ data }) {
  const rows = [{ nombre: 'Aprobadas', registros: data.aprobados, color: resultColors.aprobados }, { nombre: 'No aprobadas', registros: data.no_aprobados, color: resultColors.no_aprobados }];
  return <><div className="chart" aria-label="Distribución de los resultados de la selección"><ResponsiveContainer width="100%" height="100%"><BarChart data={rows} margin={{ top: 12, right: 12, bottom: 0, left: 0 }}><CartesianGrid strokeDasharray="3 3" vertical={false}/><XAxis dataKey="nombre" tickLine={false} axisLine={false}/><YAxis tickFormatter={number} width={65} tickLine={false} axisLine={false}/><Tooltip content={<ChartTooltip/>}/><Bar isAnimationActive={false} dataKey="registros" fill={resultColors.aprobados} radius={[5, 5, 0, 0]} maxBarSize={65}>{rows.map((row) => <Cell key={row.nombre} fill={row.color}/>)}</Bar></BarChart></ResponsiveContainer></div></>;
}

export function TrendChart({ rows }) {
  const subjects = [...new Set(rows.map((r) => r.materia))];
  const points = [...new Set(rows.map((r) => r.anio))].sort().map((anio) => {
    const point = { anio };
    for (const row of rows.filter((r) => r.anio === anio)) point[row.materia] = row.porcentaje;
    return point;
  });
  return <div className="chart" aria-label="Porcentaje de aprobación por año y materia"><ResponsiveContainer width="100%" height="100%"><LineChart data={points} margin={{ top: 12, right: 20, left: 0, bottom: 0 }}><CartesianGrid vertical={false} strokeDasharray="3 3"/><XAxis dataKey="anio" tickLine={false} axisLine={false}/><YAxis padding={{ bottom: 8, top: 5 }} domain={[0, 100]} tickFormatter={(n) => `${n}%`} width={50} tickLine={false} axisLine={false}/><Tooltip content={<ChartTooltip formatValue={percent}/>}/><Legend content={<SubjectLegend/>}/>{subjects.map((subject) => <Line isAnimationActive={false} type="linear" key={subject} dataKey={subject} stroke={subjectColors[subject] || '#0B2D66'} strokeWidth={3} strokeDasharray={subjectStyles[subject]?.dash} dot={(props) => <SubjectMarker {...props} subject={subject}/>} activeDot={(props) => <SubjectMarker {...props} subject={subject} active/>} connectNulls={false}/>)}</LineChart></ResponsiveContainer></div>;
}

export function ComparisonChart({ rows, labelKey = 'nombre' }) {
  const plotted = rows.map((row) => ({ ...row, no_aprobados: row.registros - row.aprobados }));
  return <div className="chart horizontal-chart" style={{ height: Math.max(280, rows.length * 42 + 60) }} aria-label="Comparación de resultados"><ResponsiveContainer width="100%" height="100%"><BarChart data={plotted} layout="vertical" margin={{ top: 0, right: 12, bottom: 0, left: 0 }}><CartesianGrid horizontal={false} strokeDasharray="3 3"/><XAxis type="number" tickFormatter={number} tickLine={false} axisLine={false}/><YAxis dataKey={labelKey} type="category" width={145} tick={{ fontSize: 10 }} tickLine={false} axisLine={false}/><Tooltip cursor={false} content={<ChartTooltip/>}/><Legend formatter={legendLabel} wrapperStyle={{ fontSize: 12 }}/><Bar isAnimationActive={false} dataKey="aprobados" name="Aprobadas" stackId="results" fill={resultColors.aprobados} maxBarSize={20}/><Bar isAnimationActive={false} dataKey="no_aprobados" name="No aprobadas" stackId="results" fill={resultColors.no_aprobados} maxBarSize={20}/></BarChart></ResponsiveContainer></div>;
}

export function DataTable({ headers, rows, label }) {
  return <div className="table-scroll"><table aria-label={label}><thead><tr>{headers.map((v) => <th key={v}>{v}</th>)}</tr></thead><tbody>{rows.map((row, i) => <tr key={i}>{row.map((v, j) => <td key={j}>{v}</td>)}</tr>)}</tbody></table></div>;
}
