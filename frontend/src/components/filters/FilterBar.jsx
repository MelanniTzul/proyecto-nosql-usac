import { useEffect, useState } from 'react';
import { useCatalogs } from '../common/Catalogs';
import { ErrorState } from '../common/States';
import { careerName } from '../../utils/format';

export default function FilterBar({ values, fields, onApply, onReset, label = 'Filtros de esta sección', requiredFields = [] }) {
  const catalogs = useCatalogs();
  const [draft, setDraft] = useState(values);
  const signature = JSON.stringify(values);
  useEffect(() => { setDraft(JSON.parse(signature)); }, [signature]);
  const data = catalogs?.response?.data;
  const options = {
    anio: (data?.anios || []).map((v) => [String(v), String(v)]),
    materia: (data?.materias || []).map((v) => [v, v === 'MATEMATICA' ? 'Matemática' : v === 'COMPUTACION' ? 'Computación' : 'Matemática ITUGS']),
    aprobado: [['true', 'Aprobado'], ['false', 'No aprobado']],
    carrera_id: (data?.carreras || []).filter((r) => r.id).map((r) => [r.id, careerName(r)]),
    limite: [['10', '10 evaluaciones'], ['25', '25 evaluaciones'], ['50', '50 evaluaciones'], ['100', '100 evaluaciones']],
    desde: (data?.anios || []).map((v) => [String(v), String(v)]),
    hasta: (data?.anios || []).map((v) => [String(v), String(v)]),
  };
  const labels = { anio: 'Año de ingreso', materia: 'Materia', aprobado: 'Resultado', carrera_id: 'Carrera observada', limite: 'Tamaño del subgrafo', desde: 'Desde', hasta: 'Hasta' };
  return <section className="filter-section" aria-label={label}>
    <form className="filter-bar" onSubmit={(event) => { event.preventDefault(); onApply(draft); }}>
      {fields.map((field) => <label className={`filter-field ${field === 'carrera_id' ? 'wide-field' : ''}`} key={field}>{labels[field]}
        <select required={requiredFields.includes(field)} aria-label={labels[field]} value={draft[field] ?? ''} onChange={(e) => setDraft({ ...draft, [field]: e.target.value })} disabled={catalogs?.status === 'loading' && field !== 'aprobado' && field !== 'limite'}>
          {field !== 'limite' && <option value="">{requiredFields.includes(field) ? 'Seleccionar año' : field === 'anio' ? 'Todos los años' : field === 'materia' ? 'Todas las materias' : field === 'aprobado' ? 'Todos los resultados' : field === 'carrera_id' ? 'Todas las carreras' : 'Seleccionar año'}</option>}
          {(options[field] || []).map(([value, text]) => <option value={value} key={value}>{text}</option>)}
        </select>
      </label>)}
      <div className="filter-actions"><button className="button" type="submit">Aplicar filtros <span aria-hidden="true">↗</span></button><button className="text-button" type="button" onClick={onReset}>Restablecer</button></div>
    </form>
    {catalogs?.status === 'error' && <ErrorState error={catalogs.error} retry={catalogs.retry}/>}
  </section>;
}
