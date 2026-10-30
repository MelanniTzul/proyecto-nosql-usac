import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, useLocation } from 'react-router';
import StatCards from '../components/common/StatCards';
import { EmptyState, QueryState } from '../components/common/States';
import { CatalogProvider } from '../components/common/Catalogs';
import FilterBar from '../components/filters/FilterBar';
import useFilters from '../hooks/useFilters';
import useApi from '../hooks/useApi';
import EvaluationsPage from '../pages/EvaluationsPage';

function respond(data, meta = {}) { return { ok: true, json: async () => ({ status: 'ok', data, meta }) }; }
const catalogs = { anios: [2023, 2024], materias: ['MATEMATICA', 'COMPUTACION'], carreras: [{ id: 'carrera:abc', carrera: 'MECANICA', estado: 'recortada' }] };
function mount(element) { return render(<MemoryRouter><CatalogProvider>{element}</CatalogProvider></MemoryRouter>); }
const record = (id) => ({ id, anio_ingreso: 2024, materia: 'MATEMATICA', numero_fecha_evaluacion: 1, aprobado: false, carrera: { valor: null, estado_normalizacion: 'ausente' }, advertencias: [] });

describe('Componentes y estados', () => {
  it('muestra indicadores recibidos y no inventa un porcentaje nulo', () => {
    render(<StatCards data={{ registros: 0, aprobados: 0, no_aprobados: 0, porcentaje_aprobacion: null }}/>);
    expect(screen.getByText('Sin datos')).toBeVisible(); expect(screen.getAllByText('0')).toHaveLength(3);
  });
  it('separa carga, error y respuesta vacía', async () => {
    const retry = vi.fn(); const { rerender } = render(<QueryState query={{ status: 'loading' }}>{() => null}</QueryState>);
    expect(screen.getByRole('status')).toHaveTextContent('Consultando');
    rerender(<QueryState query={{ status: 'error', error: new Error('Servicio caído'), retry }}>{() => null}</QueryState>);
    await userEvent.click(screen.getByRole('button', { name: 'Reintentar' })); expect(retry).toHaveBeenCalledOnce();
    rerender(<EmptyState/>); expect(screen.getByText('Sin resultados')).toBeVisible();
  });
  it('aplica únicamente los filtros admitidos con valores del catálogo', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(respond(catalogs)));
    const apply = vi.fn();
    mount(<FilterBar values={{ anio: '', aprobado: '' }} fields={['anio', 'aprobado']} onApply={apply} onReset={() => {}}/>);
    await waitFor(() => expect(screen.getByLabelText('Año de ingreso')).toBeEnabled());
    await userEvent.selectOptions(screen.getByLabelText('Año de ingreso'), '2024');
    await userEvent.selectOptions(screen.getByLabelText('Resultado'), 'false');
    await userEvent.click(screen.getByRole('button', { name: /Aplicar filtros/ }));
    expect(apply).toHaveBeenCalledWith({ anio: '2024', aprobado: 'false' });
    expect(screen.queryByLabelText('Carrera observada')).not.toBeInTheDocument();
  });
  it('los filtros de secciones distintas conservan parámetros independientes', async () => {
    function Example() { const [a, setA] = useFilters({ anio: '2024' }, 'carrera_'); const [b, setB] = useFilters({ anio: '2024' }, 'procedencia_'); const location = useLocation(); return <><button onClick={() => setA({ anio: '2023' })}>Carrera</button><button onClick={() => setB({ anio: '2022' })}>Procedencia</button><output>{a.anio}:{b.anio}:{location.search}</output></>; }
    render(<MemoryRouter><Example/></MemoryRouter>);
    await userEvent.click(screen.getByText('Carrera')); await userEvent.click(screen.getByText('Procedencia'));
    expect(screen.getByRole('status')).toHaveTextContent('2023:2022:');
  });
  it('ignora una respuesta atrasada al cambiar de consulta', async () => {
    let finish;
    vi.stubGlobal('fetch', vi.fn().mockImplementationOnce(() => new Promise((resolve) => { finish = resolve; })).mockResolvedValueOnce(respond('actual')));
    function Result({ url }) { const q = useApi(url); return <span>{q.response?.data || q.status}</span>; }
    const { rerender } = render(<Result url="/api/primera"/>); rerender(<Result url="/api/segunda"/>);
    expect(await screen.findByText('actual')).toBeVisible();
    finish(respond('antigua')); await new Promise((resolve) => setTimeout(resolve, 0));
    expect(screen.queryByText('antigua')).not.toBeInTheDocument();
  });
  it('pagina con el cursor y reinicia al aplicar otro año', async () => {
    const urls = [];
    vi.stubGlobal('fetch', vi.fn(async (url) => { urls.push(url); return url.includes('catalogos') ? respond(catalogs) : url.includes('cursor=') ? respond([record('segundo')], { siguiente_cursor: null }) : respond([record('primero')], { siguiente_cursor: 'cursor-seguro' }); }));
    mount(<EvaluationsPage/>);
    await userEvent.click(await screen.findByRole('button', { name: /Siguiente/ }));
    expect(await screen.findByText(/página 2/)).toBeVisible();
    expect(urls.some((url) => url.includes('cursor=cursor-seguro'))).toBe(true);
    await userEvent.selectOptions(screen.getByLabelText('Año de ingreso'), '2023');
    await userEvent.click(screen.getByRole('button', { name: /Aplicar filtros/ }));
    expect(await screen.findByText(/página 1/)).toBeVisible();
    expect(urls.at(-1)).toContain('anio=2023'); expect(urls.at(-1)).not.toContain('cursor=');
  });
});
