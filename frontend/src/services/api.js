export class ApiError extends Error {
  constructor(message, code = 'NETWORK_ERROR') { super(message); this.name = 'ApiError'; this.code = code; }
}

export function endpoint(path, params = {}) {
  const query = new URLSearchParams();
  for (const [name, value] of Object.entries(params)) {
    if (value !== '' && value !== null && value !== undefined) query.set(name, String(value));
  }
  return `/api/${path}${query.size ? `?${query}` : ''}`;
}

export async function request(url, { signal, timeout = 20000 } = {}) {
  const controller = new AbortController();
  let timedOut = false;
  const abort = () => controller.abort();
  if (signal?.aborted) controller.abort();
  signal?.addEventListener('abort', abort, { once: true });
  const timer = setTimeout(() => { timedOut = true; controller.abort(); }, timeout);
  try {
    const response = await fetch(url, { signal: controller.signal, headers: { Accept: 'application/json' } });
    let body;
    try { body = await response.json(); } catch { throw new ApiError('El servicio no devolvió una respuesta JSON válida.', 'INVALID_RESPONSE'); }
    if (!response.ok || body.status !== 'ok') {
      throw new ApiError(body.error?.message || 'No se pudo consultar el servicio.', body.error?.code || `HTTP_${response.status}`);
    }
    if (!url.startsWith('/api/health') && (!Object.hasOwn(body, 'data') || !body.meta)) throw new ApiError('La respuesta del servicio está incompleta.', 'INVALID_RESPONSE');
    return body;
  } catch (error) {
    if (signal?.aborted) throw new DOMException('Solicitud cancelada', 'AbortError');
    if (timedOut) throw new ApiError('La consulta tardó demasiado. Intenta de nuevo o reduce la selección.', 'TIMEOUT');
    if (error instanceof ApiError) throw error;
    throw new ApiError('No se pudo conectar con FastAPI. Comprueba que el backend esté disponible.');
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener('abort', abort);
  }
}

export async function getHealth(signal) { return request('/api/health', { signal }); }
