import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router';
import { CatalogProvider } from '../components/common/Catalogs';
import QueriesPage from '../pages/QueriesPage';
import QueryResultTable from '../components/common/QueryResultTable';
import catalogSource from '../../../consultas/mongodb/catalogo.json';

const mongo = catalogSource.map((q) => ({ ...q, parametros: [], valores_defecto: q.argumentos || {}, visualizacion: 'tabla' }));
const neo = [1, 2, 3, 4, 5, 6].map((id) => ({ id, titulo: `Cypher ${id}`, objetivo: 'Consulta de lectura', explicacion: 'Archivo existente', parametros: id === 4 ? ['cohorte_id'] : ['anio'], valores_defecto: id === 4 ? {} : { anio: 2024 }, visualizacion: id === 4 ? 'grafo' : 'tabla' }));
const respond = (data, fuente = 'catalogo') => ({ ok: true, json: async () => ({ status: 'ok', data, meta: { fuente } }) });
function setup() {
  const urls = [];
  vi.stubGlobal('fetch', vi.fn(async (url) => {
    urls.push(url);
    if (url === '/api/consultas') return respond({ mongodb: mongo, neo4j: neo });
    if (url === '/api/catalogos') return respond({ anios: [2024], materias: ['MATEMATICA'], carreras: [] }, 'mongodb');
    if (url.startsWith('/api/evaluaciones')) return respond([{ aspirante: { cohorte_id: '2024:' + 'a'.repeat(20) } }], 'mongodb');
    return respond({ id: Number(url.split('/').at(-1).split('?')[0]), titulo: 'Resultado comprobado', resultado: [{ registros: 7 }], filas: 1, segundos: 0.1, grafo: null }, url.includes('/neo4j/') ? 'neo4j' : 'mongodb');
  }));
  render(<MemoryRouter><CatalogProvider><QueriesPage/></CatalogProvider></MemoryRouter>);
  return urls;
}

describe('Consultas NoSQL', () => {
  it('ofrece las 30 consultas y solo ejecuta al pulsar el botón', async () => {
    const urls = setup();
    const selector = await screen.findByLabelText('Consulta del catálogo');
    expect(selector.options).toHaveLength(30);
    expect(urls.some((url) => url.includes('/consultas/mongodb/'))).toBe(false);
    await userEvent.selectOptions(selector, '24');
    await userEvent.click(screen.getByRole('button', { name: 'Ejecutar consulta' }));
    expect(await screen.findByTestId('query-result')).toHaveAttribute('data-query-id', '24');
    expect(urls).toContain('/api/consultas/mongodb/24');
    expect(screen.getByRole('table', { name: 'Resultados de consulta' })).toHaveTextContent('7');
  });
  it('ofrece seis Cypher y usa un identificador real mediante el endpoint existente', async () => {
    const urls = setup();
    await screen.findByLabelText('Consulta del catálogo');
    await userEvent.click(screen.getByRole('tab', { name: /Neo4j/ }));
    await userEvent.selectOptions(screen.getByLabelText('Consulta del catálogo'), '4');
    expect(screen.getByLabelText('Consulta del catálogo').options).toHaveLength(6);
    await userEvent.click(screen.getByRole('button', { name: /Seleccionar un identificador real/ }));
    await waitFor(() => expect(screen.getByLabelText('Aspirante de cohorte')).toHaveValue('2024:' + 'a'.repeat(20)));
    await userEvent.click(screen.getByRole('button', { name: 'Ejecutar consulta' }));
    expect(await screen.findByTestId('query-result')).toHaveAttribute('data-engine', 'neo4j');
    expect(urls.some((url) => url.includes('/consultas/neo4j/4?cohorte_id='))).toBe(true);
    expect(urls.some((url) => url.includes('cypher=') || url.includes('pipeline='))).toBe(false);
  });
  it('limpia la salida anterior al seleccionar otra consulta', async () => {
    setup();
    await screen.findByLabelText('Consulta del catálogo');
    await userEvent.click(screen.getByRole('button', { name: 'Ejecutar consulta' }));
    await screen.findByTestId('query-result');
    await userEvent.selectOptions(screen.getByLabelText('Consulta del catálogo'), '2');
    expect(screen.queryByTestId('query-result')).not.toBeInTheDocument();
    expect(screen.getByText('Elige una consulta para comenzar')).toBeVisible();
  });
  it('muestra tablas anidadas, booleanos, nulos y listas sin inventar valores', () => {
    render(<QueryResultTable value={{ truncado: true, registros: [{ aprobado: false, carrera: { valor: null } }], anios: [2024] }}/>);
    expect(screen.getAllByRole('table')).toHaveLength(3);
    expect(screen.getByText('false')).toBeVisible();
    expect(screen.getByText('Sin información')).toBeVisible();
    expect(screen.getByText('2024')).toBeVisible();
  });
});
