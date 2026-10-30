import { test, expect } from '@playwright/test';

test('histórico global identificado con filtros, patrones y tooltip accesible', async ({ page }) => {
  await page.goto('/');
  const history = page.locator('section.panel').filter({ has: page.getByRole('heading', { name: 'Evolución de la aprobación', exact: true }) });
  await expect(history.locator('.recharts-line-curve')).toHaveCount(3);
  await expect(history).toContainText('Referencia global 2015–2024.');
  await expect(history.locator('.recharts-line-dots circle').first()).toBeAttached();
  await expect(history.locator('.recharts-line-dots rect').first()).toBeAttached();
  await expect(history.locator('.recharts-line-dots path').first()).toBeAttached();
  const curves = await history.locator('.recharts-line-curve').evaluateAll((elements) => elements.map((element) => element.getAttribute('d')));
  await page.getByLabel('Año de ingreso').selectOption('2024');
  await page.getByLabel('Materia', { exact: true }).selectOption('MATEMATICA');
  await page.getByLabel('Resultado', { exact: true }).selectOption('true');
  const filtered = page.waitForResponse((response) => response.url().includes('/api/estadisticas?') && response.url().includes('aprobado=true'));
  await page.getByRole('button', { name: /Aplicar filtros/ }).click();
  expect((await filtered).status()).toBe(200);
  await expect(history.locator('.recharts-line-curve')).toHaveCount(3);
  expect(await history.locator('.recharts-line-curve').evaluateAll((elements) => elements.map((element) => element.getAttribute('d')))).toEqual(curves);
  await expect(history).toContainText('Los filtros superiores afectan a los indicadores y a la distribución de resultados, no a esta gráfica.');
  await history.locator('svg.recharts-surface').first().focus();
  await page.keyboard.press('ArrowRight');
  const historicalTooltip = history.locator('.recharts-tooltip-wrapper');
  await expect(historicalTooltip).toBeVisible();
  await expect(historicalTooltip).toContainText('COMPUTACION');
  await expect(historicalTooltip).toContainText('%');
  const distribution = page.locator('section.panel').filter({ has: page.getByRole('heading', { name: 'Distribución de resultados', exact: true }) });
  await distribution.locator('svg.recharts-surface').first().focus();
  await page.keyboard.press('ArrowRight');
  await expect(distribution.locator('.recharts-tooltip-wrapper')).toBeVisible();
  await expect(distribution.locator('.recharts-tooltip-wrapper')).toContainText(/Aprobadas|No aprobadas/);
});

test('cada categoría del subgrafo real se identifica por texto en leyenda e inspector', async ({ page }) => {
  await page.goto('/grafo');
  await expect(page.locator('.graph-canvas canvas').first()).toBeVisible();
  const categories = await page.locator('.graph-legend > span').allTextContents();
  expect(categories.length).toBeGreaterThan(0);
  await page.getByText('Lista accesible de nodos y relaciones', { exact: true }).click();
  const inspector = page.getByRole('complementary', { name: 'Propiedades del nodo seleccionado' });
  for (const category of categories) {
    const node = page.locator('.node-list-item').filter({ hasText: `${category} ·` }).first();
    await node.click();
    await expect(inspector.getByRole('heading', { name: category, exact: true })).toBeVisible();
    await expect(inspector.locator('dd').first()).toBeVisible();
  }
});
