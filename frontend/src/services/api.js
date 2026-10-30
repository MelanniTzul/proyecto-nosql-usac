export async function getHealth(signal) {
  const response = await fetch('/api/health', { signal });
  if (!response.ok) throw new Error('La API respondió con un error.');
  const data = await response.json();
  if (data.status !== 'ok' || data.service !== 'usac-admisiones-api') {
    throw new Error('La respuesta de la API no tiene el formato esperado.');
  }
  return data;
}
