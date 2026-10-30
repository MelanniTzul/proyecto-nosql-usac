import { useEffect, useRef, useState } from 'react';
import useApi from '../hooks/useApi';
import { endpoint, request } from '../services/api';
import { useCatalogs } from '../components/common/Catalogs';
import { PageHeading, QueryState, ErrorState } from '../components/common/States';
import QueryResultTable from '../components/common/QueryResultTable';
import { GraphView } from './GraphPage';

const labels = { anio: 'Año de ingreso', desde: 'Desde', hasta: 'Hasta', materia: 'Materia',
  aprobado: 'Resultado', carrera_id: 'Carrera observada', cohorte_id: 'Aspirante de cohorte' };

export default function QueriesPage() {
  const catalog = useApi('/api/consultas');
  const domains = useCatalogs();
  const [engine, setEngine] = useState('mongodb');
  const [identity, setIdentity] = useState('1');
  const [params, setParams] = useState({});
  const [execution, setExecution] = useState(null);
  const [cohortLoading, setCohortLoading] = useState(false);
  const [cohortError, setCohortError] = useState(null);
  const cohortPreset = useRef(null);
  const list = catalog.response?.data?.[engine] || [];
  const selected = list.find((q) => String(q.id) === identity);
  const careers = domains.response?.data?.carreras || [];
  const years = domains.response?.data?.anios || [];
  const subjects = domains.response?.data?.materias || [];
  const current = execution?.engine === engine && execution?.id === identity ? execution : null;
  const result = useApi(current?.url || null, 70000);
  const annualCareers = useApi(engine === 'neo4j' && identity === '3' && params.anio && params.materia
    ? endpoint('resultados/carreras', { anio: params.anio, materia: params.materia }) : null);

  useEffect(() => {
    if (!selected) return;
    const defaults = Object.fromEntries(Object.entries(selected.valores_defecto).map(([key, value]) => [key, String(value)]));
    if (cohortPreset.current && selected.id === 4 && selected.parametros.includes('cohorte_id')) {
      defaults.cohorte_id = cohortPreset.current; cohortPreset.current = null;
    }
    setParams(defaults);
  }, [selected]);
  useEffect(() => {
    if (engine === 'neo4j' && identity === '3' && !params.carrera_id && annualCareers.status === 'success') {
      const career = annualCareers.response.data.find((c) => c.id);
      if (career) setParams((previous) => ({ ...previous, carrera_id: career.id }));
    }
  }, [engine, identity, annualCareers.status, annualCareers.response, params.carrera_id]);

  function select(engineName, queryId = '1') {
    cohortPreset.current = null;
    setExecution(null); setEngine(engineName); setIdentity(queryId); setCohortError(null);
  }
  function changeParameter(field, value) {
    setParams({ ...params, [field]: value, ...(identity === '3' && ['anio', 'materia'].includes(field) ? { carrera_id: '' } : {}) });
    setExecution(null);
  }
  function execute(event) {
    event.preventDefault();
    const values = engine === 'neo4j' ? Object.fromEntries(selected.parametros.map((key) => [key, params[key]])) : {};
    const url = endpoint(`consultas/${engine}/${identity}`, values);
    if (current?.url === url) result.retry();
    else setExecution({ engine, id: identity, url });
  }
  async function realCohort() {
    setCohortLoading(true); setCohortError(null);
    try {
      const response = await request(endpoint('evaluaciones', { anio: 2024, limite: 1 }));
      const value = response.data[0]?.aspirante.cohorte_id;
      if (!value) throw new Error('No se encontró una cohorte en la selección.');
      setParams((previous) => ({ ...previous, cohorte_id: value }));
    } catch (error) { setCohortError(error); }
    finally { setCohortLoading(false); }
  }
  function showCohort(id) {
    cohortPreset.current = engine === 'neo4j' && identity === '4' ? null : id;
    setEngine('neo4j'); setIdentity('4');
    // El id viene del nodo real, nunca del texto de una consulta.
    setParams({ cohorte_id: id });
    setExecution({ engine: 'neo4j', id: '4', url: endpoint('consultas/neo4j/4', { cohorte_id: id }) });
  }
  return <><PageHeading eyebrow="ANÁLISIS DISPONIBLES" title="Consultas NoSQL" description="Selecciona un análisis y consulta sus resultados."/>
    <div className="query-tabs" role="tablist" aria-label="Motor de consultas"><button role="tab" aria-selected={engine === 'mongodb'} onClick={() => select('mongodb')}>MongoDB · 30 consultas</button><button role="tab" aria-selected={engine === 'neo4j'} onClick={() => select('neo4j')}>Neo4j · 6 consultas</button></div>
    <QueryState query={catalog}>{() => <section className="panel query-selection" role="tabpanel" aria-label={engine === 'mongodb' ? 'Consultas MongoDB' : 'Consultas Neo4j'}><form onSubmit={execute}>
      <label className="query-selector">Consulta del catálogo<select aria-label="Consulta del catálogo" value={identity} onChange={(event) => select(engine, event.target.value)}>{list.map((q) => <option value={q.id} key={q.id}>{String(q.id).padStart(2, '0')}. {q.titulo}</option>)}</select></label>
      {selected && <><h2>{selected.titulo}</h2><p className="page-description">{selected.objetivo}</p><p className="method-note query-explanation">{engine === 'mongodb' ? selected.explicacion : 'Los resultados corresponden a los filtros seleccionados.'}</p>
      {engine === 'mongodb' ? <p className="info-note">Se ejecuta la consulta existente con sus parámetros predefinidos: {Object.keys(selected.valores_defecto).length ? JSON.stringify(selected.valores_defecto) : 'conjunto completo, según la definición del catálogo'}. La consulta 24 puede tardar hasta un minuto.</p> : <div className="query-parameters">{selected.parametros.map((field) => <label className="filter-field" key={field}>{labels[field]}
        {field === 'cohorte_id' ? <input required aria-label={labels[field]} value={params[field] || ''} maxLength={37} pattern="(201[5-9]|202[0-4]):[0-9a-f]{20,32}" onChange={(event) => changeParameter(field, event.target.value)} placeholder="año:correlativo"/> : <select required aria-label={labels[field]} value={params[field] ?? ''} onChange={(event) => changeParameter(field, event.target.value)}>
          <option value="">Seleccionar</option>
          {['anio', 'desde', 'hasta'].includes(field) && years.map((year) => <option key={year} value={year}>{year}</option>)}
          {field === 'materia' && subjects.map((subject) => <option key={subject}>{subject}</option>)}
          {field === 'aprobado' && <><option value="true">Aprobado</option><option value="false">No aprobado</option></>}
          {field === 'carrera_id' && careers.filter((c) => c.id).map((career) => <option key={career.id} value={career.id}>{career.carrera}{career.estado === 'recortada' ? ' · recortada' : ''}</option>)}
        </select>}
      </label>)}</div>}
      {engine === 'neo4j' && identity === '4' && <button className="button secondary" type="button" onClick={realCohort} disabled={cohortLoading}>{cohortLoading ? 'Consultando identificador…' : 'Seleccionar un identificador real de 2024'}</button>}
      {cohortError && <ErrorState error={cohortError} retry={realCohort}/>}
      {engine === 'neo4j' && identity === '3' && annualCareers.status === 'error' && <ErrorState error={annualCareers.error} retry={annualCareers.retry}/>}
      {engine === 'neo4j' && domains.status === 'error' && <ErrorState error={domains.error} retry={domains.retry}/>}
      <div className="query-actions"><button className="button" type="submit" disabled={result.status === 'loading' || cohortLoading || (engine === 'neo4j' && domains.status === 'loading') || (engine === 'neo4j' && identity === '3' && annualCareers.status === 'loading')}>{result.status === 'loading' ? 'Ejecutando consulta…' : 'Ejecutar consulta'}</button><span className="method-note">Máximo 500 filas por lista; se mantienen los límites de la consulta original.</span></div>
      </>}
    </form></section>}</QueryState>
    {result.status === 'idle' && <section className="panel query-idle"><h2>Elige una consulta para comenzar</h2><p>Los resultados aparecerán aquí después de pulsar Ejecutar consulta.</p></section>}
    <QueryState query={result}>{(data, meta) => <section className="panel query-results" data-testid="query-result" data-engine={engine} data-query-id={data.id}><div className="panel-heading"><div><p className="eyebrow">CONSULTA {String(data.id).padStart(2, '0')}</p><h2>{data.titulo}</h2><p>{data.filas} filas / registros de salida · {data.segundos} segundos</p></div><span className="badge success">Ejecución correcta</span></div>
      {meta.truncado && <p className="info-note">Resultado limitado por la consulta original o por el máximo de respuesta. No representa un conteo total adicional.</p>}
      {data.grafo?.nodes.length > 0 && <GraphView data={data.grafo} meta={meta} onCohort={showCohort} canReturn={false} onReturn={() => {}}/>}
      <QueryResultTable value={data.resultado}/>
    </section>}</QueryState>
    <p className="method-note">Los resultados conservan ausencias, textos recortados y repeticiones originales. Aspirante de cohorte significa año + correlativo.</p>
  </>;
}
