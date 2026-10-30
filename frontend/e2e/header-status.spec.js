import { test, expect } from '@playwright/test';

test('el botón comprueba estado, muestra carga y no vuelve a consultar estadísticas', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByText('Sistema disponible', { exact: true })).toBeVisible();
  await expect(page.locator('.recharts-line-curve')).toHaveCount(3);
  await expect(page.getByLabel('Año de ingreso')).toBeEnabled();
  const values = await page.locator('.stat-value').allTextContents();
  const urls = [];
  page.on('request', (request) => { const path = new URL(request.url()).pathname; if (path.startsWith('/api/')) urls.push(path); });
  const button = page.getByRole('button', { name: 'Comprobar conexión' });
  await button.focus();
  await expect(page.getByRole('tooltip')).toBeVisible();
  await expect(button).toHaveAccessibleDescription('Comprueba el estado de las conexiones. No actualiza los datos de las pantallas.');
  let release;
  await page.route('**/api/health/databases', async (route) => {
    await new Promise((resolve) => { release = resolve; });
    await route.continue();
  }, { times: 1 });
  const pending = page.waitForRequest('**/api/health/databases');
  await button.click();
  await pending;
  await expect(button).toBeDisabled();
  await expect(button).toHaveAttribute('aria-busy', 'true');
  await expect(page.getByText('Comprobando estado…', { exact: true })).toBeVisible();
  release();
  await expect(page.getByText('Estado actualizado', { exact: true })).toBeVisible();
  await expect(button).toBeEnabled();
  expect(await page.locator('.stat-value').allTextContents()).toEqual(values);
  expect(urls).toEqual(['/api/health/databases']);
  await page.route('**/api/health/databases', (route) => route.abort(), { times: 1 });
  await button.click();
  await expect(page.getByText('No se pudo comprobar el estado. Intenta nuevamente.')).toBeVisible();
  await button.click();
  await expect(page.getByText('Estado actualizado', { exact: true })).toBeVisible();
  await expect(page.getByText('Sistema disponible', { exact: true })).toBeVisible();
  expect(urls).toEqual(Array(3).fill('/api/health/databases'));
  for (const width of [390, 320]) {
    await page.setViewportSize({ width, height: 844 });
    await expect(button.getByText('Comprobar conexión', { exact: true })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    const header = await page.locator('.app-header').boundingBox();
    const bounds = await button.boundingBox();
    expect(bounds.x + bounds.width).toBeLessThanOrEqual(header.x + header.width);
    expect(bounds.y + bounds.height).toBeLessThanOrEqual(header.y + header.height);
    await page.getByRole('button', { name: 'Abrir navegación' }).click();
    await expect(page.getByRole('navigation', { name: 'Navegación principal' })).toBeVisible();
    await page.getByRole('button', { name: 'Cerrar navegación' }).click({ position: { x: width - 10, y: 100 } });
  }
});
