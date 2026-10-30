// Cada id se ejecuta y se comprueba en React con respuestas reales, sin fixtures.
import { test, expect } from '@playwright/test';

test('las 30 consultas MongoDB se ejecutan y muestran resultados en React', async ({ page }) => {
  test.setTimeout(240000);
  const errors = []; page.on('pageerror', (error) => errors.push(error.message));
  await page.goto('/consultas');
  const select = page.getByLabel('Consulta del catálogo');
  await expect(select.locator('option')).toHaveCount(30);
  for (let id = 1; id <= 30; id++) {
    await select.selectOption(String(id));
    const response = page.waitForResponse((r) => new URL(r.url()).pathname === `/api/consultas/mongodb/${id}`, { timeout: 75000 });
    await page.getByRole('button', { name: 'Ejecutar consulta', exact: true }).click();
    const loaded = await response;
    expect(loaded.status(), `MongoDB ${id}`).toBe(200);
    const result = page.getByTestId('query-result');
    await expect(result).toHaveAttribute('data-query-id', String(id));
    await expect(result).toHaveAttribute('data-engine', 'mongodb');
    await expect(result.getByText('Ejecución correcta')).toBeVisible();
    expect(await result.getByRole('table').count(), `Tabla MongoDB ${id}`).toBeGreaterThan(0);
    if (id === 24) await expect(result.getByRole('table')).toContainText('834');
  }
  expect(errors).toEqual([]);
});

test('las seis Cypher se ejecutan en Neo4j y muestran tablas o grafos', async ({ page }) => {
  test.setTimeout(180000);
  const errors = []; page.on('pageerror', (error) => errors.push(error.message));
  await page.goto('/consultas');
  await expect(page.getByLabel('Consulta del catálogo')).toBeVisible();
  await page.getByRole('tab', { name: /Neo4j/ }).click();
  const select = page.getByLabel('Consulta del catálogo');
  await expect(select.locator('option')).toHaveCount(6);
  for (let id = 1; id <= 6; id++) {
    await select.selectOption(String(id));
    if (id === 4) {
      await page.getByRole('button', { name: /Seleccionar un identificador real/ }).click();
      await expect(page.getByLabel('Aspirante de cohorte')).toHaveValue(/^2024:/);
    }
    const response = page.waitForResponse((r) => new URL(r.url()).pathname === `/api/consultas/neo4j/${id}`);
    await page.getByRole('button', { name: 'Ejecutar consulta', exact: true }).click();
    const loaded = await response;
    expect(loaded.status(), `Neo4j ${id}`).toBe(200);
    const result = page.getByTestId('query-result');
    await expect(result).toHaveAttribute('data-query-id', String(id));
    await expect(result).toHaveAttribute('data-engine', 'neo4j');
    await expect(result.getByRole('table').first()).toBeVisible();
    if (id === 3 || id === 4) await expect(result.locator('.graph-canvas canvas').first()).toBeVisible();
  }
  expect(errors).toEqual([]);
});
