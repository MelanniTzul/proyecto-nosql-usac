import { DataTable } from '../charts/Charts';
import { EmptyState } from './States';

function flatten(object, prefix = '') {
  const output = {};
  for (const [name, value] of Object.entries(object)) {
    const key = prefix ? `${prefix}.${name}` : name;
    if (value !== null && typeof value === 'object' && !Array.isArray(value)) Object.assign(output, flatten(value, key));
    else output[key] = value;
  }
  return output;
}
function cell(value) {
  if (value === null || value === undefined) return 'Sin información';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}
export default function QueryResultTable({ value, label = 'Resultados de consulta' }) {
  if (Array.isArray(value)) {
    if (!value.length) return <EmptyState message="La consulta se ejecutó correctamente y no devolvió filas."/>;
    const rows = value.map((row) => row !== null && typeof row === 'object' && !Array.isArray(row) ? flatten(row) : { valor: row });
    const columns = [...new Set(rows.flatMap((row) => Object.keys(row)))];
    return <DataTable label={label} headers={columns.map((name) => name.replaceAll('_', ' '))} rows={rows.map((row) => columns.map((name) => cell(row[name])))}/>;
  }
  if (value !== null && typeof value === 'object') {
    const scalars = Object.fromEntries(Object.entries(value).filter(([, item]) => !Array.isArray(item)));
    const arrays = Object.entries(value).filter(([, item]) => Array.isArray(item));
    return <>{Object.keys(scalars).length > 0 && <QueryResultTable value={[scalars]} label={label}/>} {arrays.map(([name, rows]) => <section className="query-result-section" key={name}><h3>{name.replaceAll('_', ' ')}</h3><QueryResultTable value={rows} label={`${label}: ${name}`}/></section>)}</>;
  }
  return <DataTable label={label} headers={['Valor']} rows={[[cell(value)]]}/>;
}
