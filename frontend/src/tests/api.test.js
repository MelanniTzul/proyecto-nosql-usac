import { describe, it, expect, vi } from 'vitest';
import { endpoint, request } from '../services/api';
const payload = { status: 'ok', data: [], meta: { fuente: 'mongodb' } };
describe('Cliente de API', () => {
  it('conserva false, omite filtros vacíos y codifica el cursor', () => {
    expect(endpoint('evaluaciones', { anio: '', aprobado: false, cursor: 'a+b=' })).toBe('/api/evaluaciones?aprobado=false&cursor=a%2Bb%3D');
  });
  it('consume JSON real sin sustituir respuestas vacías', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => payload }));
    expect(await request('/api/evaluaciones')).toEqual(payload);
  });
  it('muestra el error seguro de FastAPI', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, json: async () => ({ status: 'error', error: { message: 'Filtros inválidos', code: 'INVALID_PARAMETERS' } }) }));
    await expect(request('/api/evaluaciones')).rejects.toMatchObject({ message: 'Filtros inválidos', code: 'INVALID_PARAMETERS' });
  });
  it('rechaza respuestas incompletas sin inventar datos', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({ status: 'ok' }) }));
    await expect(request('/api/estadisticas')).rejects.toHaveProperty('code', 'INVALID_RESPONSE');
  });
  it('distingue un fallo de red', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('fetch failed')));
    await expect(request('/api/estadisticas')).rejects.toHaveProperty('code', 'NETWORK_ERROR');
  });
  it('cancela solicitudes sin convertirlas en resultados', async () => {
    const controller = new AbortController();
    vi.stubGlobal('fetch', vi.fn((url, { signal }) => new Promise((resolve, reject) => signal.addEventListener('abort', () => reject(new DOMException('', 'AbortError'))))));
    const pending = request('/api/evaluaciones', { signal: controller.signal }); controller.abort();
    await expect(pending).rejects.toHaveProperty('name', 'AbortError');
  });
  it('permite el contrato anterior de salud', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({ status: 'ok', service: 'usac-admisiones-api' }) }));
    expect((await request('/api/health')).service).toBe('usac-admisiones-api');
  });
});
