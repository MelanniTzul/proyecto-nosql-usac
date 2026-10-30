// Navegador real + endpoints reales. Ninguna respuesta estadística se simula aquí.
import { test, expect } from '@playwright/test';
import { mkdir } from 'node:fs/promises';
const shots = '../data/reports/etapa-6';
let errors;
test.beforeEach(async ({ page }) => { errors = []; page.on('pageerror', (error) => errors.push(error.message)); await mkdir(shots, { recursive: true }); });
test.afterEach(() => { expect(errors).toEqual([]); });

test('dashboard con datos reales, filtros y navegación', async ({ page, request }) => {
  const response = await request.get('/api/estadisticas'); const { data } = await response.json();
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Panorama de admisión' })).toBeVisible();
  await expect(page.locator('.stat-value').first()).toHaveText(new Intl.NumberFormat('es-GT').format(data.registros));
  await expect(page.locator('.recharts-surface').first()).toBeVisible();
  await expect(page.getByText('Sistema disponible')).toBeVisible();
  await page.screenshot({ path: `${shots}/dashboard-desktop.png`, fullPage: true });
  await page.getByLabel('Año de ingreso').selectOption('2024');
  await page.getByLabel('Materia', { exact: true }).selectOption('MATEMATICA');
  await page.getByLabel('Resultado', { exact: true }).selectOption('false');
  const loaded = page.waitForResponse((r) => r.url().includes('/api/estadisticas?') && r.url().includes('aprobado=false'));
  await page.getByRole('button', { name: /Aplicar filtros/ }).click();
  const filtered = (await (await loaded).json()).data;
  await expect(page.locator('.stat-value').first()).toHaveText(new Intl.NumberFormat('es-GT').format(filtered.registros));
  await expect(page.locator('.stat-value').nth(1)).toHaveText('0');
  await expect(page).toHaveURL(/aprobado=false/);
  await page.getByRole('link', { name: /Estadísticas/ }).click();
  await expect(page.getByRole('heading', { name: 'Resultados en perspectiva' })).toBeVisible();
  await expect(page.getByRole('table', { name: 'Resultados por carrera' })).toBeVisible();
  await page.screenshot({ path: `${shots}/estadisticas-desktop.png`, fullPage: true });
});

test('evaluaciones: cursor, retroceso y reinicio de filtros', async ({ page }) => {
  await page.goto('/evaluaciones');
  await expect(page.getByRole('table', { name: 'Evaluaciones de admisión' })).toBeVisible();
  const first = await page.locator('tbody tr button').first().getAttribute('aria-label');
  await page.getByRole('button', { name: /Siguiente/ }).click();
  await expect(page.getByText(/página 2/)).toBeVisible();
  expect(await page.locator('tbody tr button').first().getAttribute('aria-label')).not.toBe(first);
  await page.getByRole('button', { name: /Anterior/ }).click();
  await expect(page.getByText(/página 1/)).toBeVisible();
  expect(await page.locator('tbody tr button').first().getAttribute('aria-label')).toBe(first);
  await page.getByLabel('Año de ingreso').selectOption('2024');
  await page.getByRole('button', { name: /Aplicar filtros/ }).click();
  await expect(page.locator('tbody tr td:first-child').first()).toHaveText('2024');
  await page.locator('tbody tr button').first().click();
  await expect(page.getByRole('region', { name: 'Detalle de evaluación' })).toBeVisible();
  await page.screenshot({ path: `${shots}/evaluaciones-desktop.png`, fullPage: true });
});

test('grafo Neo4j real: canvas, controles y selección accesible', async ({ page }) => {
  await page.goto('/grafo');
  await expect(page.locator('.graph-canvas canvas').first()).toBeVisible();
  await expect(page.locator('.graph-summary')).toContainText('25 evaluaciones');
  await expect(page.getByText(/Subgrafo parcial/)).toBeVisible();
  await page.getByRole('button', { name: 'Acercar grafo' }).click();
  await page.getByRole('button', { name: 'Ajustar grafo al área visible' }).click();
  await page.getByText('Lista accesible de nodos y relaciones', { exact: true }).click();
  await page.locator('.node-list-item').filter({ hasText: 'Aspirante de cohorte' }).first().click();
  await expect(page.getByRole('button', { name: /Consultar esta cohorte/ })).toBeVisible();
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: `${shots}/grafo-desktop.png`, fullPage: true });
  await page.getByRole('button', { name: /Consultar esta cohorte/ }).click();
  await expect(page.getByText(/Vista del aspirante de cohorte/)).toBeVisible();
  await expect(page.getByRole('button', { name: /Volver a filtros/ })).toBeVisible();
});

test('móvil: navegación, gráficos y tabla sin desbordamiento global', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');
  await expect(page.locator('.stat-value').first()).not.toHaveText('—');
  await expect(page.locator('.stat-value')).toHaveCount(4);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: `${shots}/dashboard-mobile.png`, fullPage: true });
  await page.getByRole('button', { name: 'Abrir navegación' }).click();
  await page.getByRole('link', { name: /Explorador de grafos/ }).click();
  await expect(page.locator('.graph-canvas canvas').first()).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: `${shots}/grafo-mobile.png`, fullPage: true });
});

test('un fallo HTTP muestra reintento y recupera los datos reales', async ({ page }) => {
  // Solo se provoca indisponibilidad; la recuperación usa la respuesta real del servidor.
  await page.route('**/api/estadisticas', (route) => route.abort());
  await page.goto('/');
  await expect(page.getByRole('alert')).toContainText('No pudimos completar la consulta');
  await page.unroute('**/api/estadisticas');
  await page.getByRole('button', { name: 'Reintentar' }).click();
  await expect(page.locator('.stat-value').first()).not.toHaveText('—');
});

test('estadísticas: cada sección conserva filtros propios', async ({ page, request }) => {
  await page.goto('/estadisticas');
  const careers = page.locator('section.panel').filter({ has: page.getByRole('heading', { name: 'Resultados por carrera', exact: true }) });
  const provenance = page.locator('section.panel').filter({ has: page.getByRole('heading', { name: 'Procedencia educativa', exact: true }) });
  await expect(careers.getByRole('table')).toBeVisible();
  await careers.getByLabel('Año de ingreso').selectOption('2023');
  await careers.getByLabel('Materia', { exact: true }).selectOption('COMPUTACION');
  const changed = page.waitForResponse((r) => r.url().includes('/api/resultados/carreras?anio=2023&materia=COMPUTACION'));
  await careers.getByRole('button', { name: /Aplicar filtros/ }).click();
  const body = await (await changed).json();
  await expect(careers.locator('tbody tr')).toHaveCount(body.data.length);
  await expect(provenance.getByLabel('Año de ingreso')).toHaveValue('2024');
  const history = page.locator('section.panel').filter({ has: page.getByRole('heading', { name: 'Aprobación por año y materia', exact: true }) });
  await history.getByLabel('Desde', { exact: true }).selectOption('2023');
  await history.getByLabel('Hasta', { exact: true }).selectOption('2024');
  await history.getByRole('button', { name: /Aplicar filtros/ }).click();
  await history.getByText('Ver tabla histórica', { exact: true }).click();
  const expected = await (await request.get('/api/estadisticas/aprobacion?desde=2023&hasta=2024')).json();
  await expect(history.locator('tbody tr')).toHaveCount(expected.data.length);
  await expect(careers.getByLabel('Año de ingreso')).toHaveValue('2023');
});

test('grafo: aplica materia, resultado y carrera de un registro real', async ({ page, request }) => {
  const record = (await (await request.get('/api/evaluaciones?anio=2024&limite=1')).json()).data[0];
  const catalog = (await (await request.get('/api/catalogos')).json()).data;
  const career = catalog.carreras.find((c) => c.carrera === record.carrera.valor && c.estado === record.carrera.estado_normalizacion);
  await page.goto('/grafo');
  await expect(page.locator('.graph-canvas canvas').first()).toBeVisible();
  await page.getByLabel('Materia', { exact: true }).selectOption(record.materia);
  await page.getByLabel('Resultado', { exact: true }).selectOption(String(record.aprobado));
  await page.getByLabel('Carrera observada', { exact: true }).selectOption(career.id);
  await page.getByLabel('Tamaño del subgrafo').selectOption('10');
  const loaded = page.waitForResponse((r) => r.url().includes('/api/grafo?') && r.url().includes('carrera_id='));
  await page.getByRole('button', { name: /Aplicar filtros/ }).click();
  const body = await (await loaded).json();
  expect(body.data.nodes.some((n) => n.tipo === 'Evaluacion')).toBe(true);
  expect(body.data.nodes.filter((n) => n.tipo === 'Evaluacion').every((n) => n.properties.aprobado === record.aprobado)).toBe(true);
  await expect(page.locator('.graph-canvas canvas').first()).toBeVisible();
  await expect(page.locator('.graph-summary')).toContainText(`${body.data.nodes.length} nodos`);
});

test('una selección real sin registros muestra vacío y porcentaje sin datos', async ({ page }) => {
  await page.goto('/?anio=2015&materia=MATEMATICA%20ITUGS');
  await expect(page.locator('.stat-value').first()).toHaveText('0');
  await expect(page.locator('.stat-value').nth(3)).toHaveText('Sin datos');
  await expect(page.getByText('Sin resultados', { exact: true })).toBeVisible();
  await page.goto('/grafo?anio=2015&materia=MATEMATICA%20ITUGS');
  await expect(page.getByText('Sin resultados', { exact: true })).toBeVisible();
  await expect(page.locator('.graph-canvas')).toHaveCount(0);
});
