import { number, percent } from '../../utils/format';
export default function StatCards({ data }) {
  const items = [
    ['Total de evaluaciones', number(data.registros), 'Registros de la selección', 'total', '↗'],
    ['Aprobadas', number(data.aprobados), 'Resultado aprobado', 'approved', '✓'],
    ['No aprobadas', number(data.no_aprobados), 'Resultado no aprobado', 'rejected', '−'],
    ['Porcentaje de aprobación', percent(data.porcentaje_aprobacion), 'Aprobadas / total de registros', 'rate', '%'],
  ];
  return <div className="stat-grid">{items.map(([label, value, detail, style, symbol]) => <article className={`stat-card ${style}`} key={label}><div className="stat-label">{label}<span className="stat-icon" aria-hidden="true">{symbol}</span></div><strong className="stat-value">{value}</strong><p>{detail}</p></article>)}</div>;
}
