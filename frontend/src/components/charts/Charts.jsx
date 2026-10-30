import { ResponsiveContainer, BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { number, percent } from '../../utils/format';
const colors = ['#287b83', '#426fb2', '#b58a3a'];

export function ChartPanel({ title, subtitle, children, table, className = '' }) {
  return <section className={`panel ${className}`}><div className="panel-heading"><div><h2>{title}</h2><p>{subtitle}</p></div><span className="panel-mark" aria-hidden="true">↗</span></div>{children}{table && <details className="data-details"><summary>Ver tabla de datos</summary>{table}</details>}</section>;
}

export function ResultChart({ data }) {
  const rows = [{ nombre: 'Aprobadas', registros: data.aprobados }, { nombre: 'No aprobadas', registros: data.no_aprobados }];
  return <><div className="chart" aria-label="Distribución de los resultados de la selección"><ResponsiveContainer width="100%" height="100%"><BarChart data={rows} margin={{ top: 12, right: 12, bottom: 0, left: 0 }}><CartesianGrid strokeDasharray="3 3" vertical={false}/><XAxis dataKey="nombre" tickLine={false} axisLine={false}/><YAxis tickFormatter={number} width={65} tickLine={false} axisLine={false}/><Tooltip formatter={(value) => [number(value), 'Evaluaciones']}/><Bar isAnimationActive={false} dataKey="registros" fill="#287b83" radius={[5, 5, 0, 0]} maxBarSize={65}/></BarChart></ResponsiveContainer></div><p className="chart-footnote">Distribución de los registros, no de personas únicas.</p></>;
}

export function TrendChart({ rows }) {
  const subjects = [...new Set(rows.map((r) => r.materia))];
  const points = [...new Set(rows.map((r) => r.anio))].sort().map((anio) => {
    const point = { anio };
    for (const row of rows.filter((r) => r.anio === anio)) point[row.materia] = row.porcentaje;
    return point;
  });
  return <div className="chart" aria-label="Porcentaje de aprobación por año y materia"><ResponsiveContainer width="100%" height="100%"><LineChart data={points} margin={{ top: 12, right: 20, left: 0, bottom: 0 }}><CartesianGrid vertical={false} strokeDasharray="3 3"/><XAxis dataKey="anio" tickLine={false} axisLine={false}/><YAxis domain={[0, 100]} tickFormatter={(n) => `${n}%`} width={50} tickLine={false} axisLine={false}/><Tooltip formatter={(v, name) => [percent(v), name]}/><Legend iconType="circle" wrapperStyle={{ fontSize: 11 }}/>{subjects.map((subject, i) => <Line isAnimationActive={false} type="linear" key={subject} dataKey={subject} stroke={colors[i % colors.length]} strokeWidth={2.5} dot={{ r: 3 }} connectNulls={false}/>)}</LineChart></ResponsiveContainer></div>;
}

export function ComparisonChart({ rows, labelKey = 'nombre' }) {
  const plotted = rows.map((row) => ({ ...row, no_aprobados: row.registros - row.aprobados }));
  return <div className="chart horizontal-chart" style={{ height: Math.max(280, rows.length * 42 + 60) }} aria-label="Comparación de resultados"><ResponsiveContainer width="100%" height="100%"><BarChart data={plotted} layout="vertical" margin={{ top: 0, right: 12, bottom: 0, left: 0 }}><CartesianGrid horizontal={false} strokeDasharray="3 3"/><XAxis type="number" tickFormatter={number} tickLine={false} axisLine={false}/><YAxis dataKey={labelKey} type="category" width={145} tick={{ fontSize: 10 }} tickLine={false} axisLine={false}/><Tooltip formatter={(v, name) => [number(v), name]}/><Legend wrapperStyle={{ fontSize: 12 }}/><Bar isAnimationActive={false} dataKey="aprobados" name="Aprobadas" stackId="results" fill="#287b83" maxBarSize={20}/><Bar isAnimationActive={false} dataKey="no_aprobados" name="No aprobadas" stackId="results" fill="#c4cfdb" maxBarSize={20}/></BarChart></ResponsiveContainer></div>;
}

export function DataTable({ headers, rows, label }) {
  return <div className="table-scroll"><table aria-label={label}><thead><tr>{headers.map((v) => <th key={v}>{v}</th>)}</tr></thead><tbody>{rows.map((row, i) => <tr key={i}>{row.map((v, j) => <td key={j}>{v}</td>)}</tr>)}</tbody></table></div>;
}
