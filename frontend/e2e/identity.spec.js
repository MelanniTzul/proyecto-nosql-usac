import { test, expect } from '@playwright/test';

test('escudo USAC y favicon sin deformación en escritorio y móvil', async ({ page, request }) => {
  await page.goto('/');
  const shield = page.getByRole('img', { name: 'Escudo de la USAC' });
  await expect(shield).toBeVisible();
  await expect(shield).toHaveAttribute('src', '/escudo-usac.png');
  expect(await shield.evaluate((image) => ({ width: image.naturalWidth, height: image.naturalHeight })))
    .toEqual({ width: 246, height: 246 });
  const bounds = await shield.boundingBox();
  expect(bounds.width).toBe(bounds.height);
  await expect(page.locator('.brand')).toContainText('ADMISIONESUSAC');
  await expect(page.locator('body')).not.toContainText(/CUNOC/i);
  const favicon = page.locator('link[rel="icon"]');
  await expect(favicon).toHaveAttribute('href', '/escudo-usac.png');
  const response = await request.get('/escudo-usac.png');
  expect(response.status()).toBe(200);
  expect(response.headers()['content-type']).toContain('image/png');
  expect((await response.body()).subarray(0, 8).toString('hex')).toBe('89504e470d0a1a0a');
  await page.screenshot({ path: '../data/reports/etapa-6/identidad-desktop.png', fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole('button', { name: 'Abrir navegación' }).click();
  await expect(shield).toBeVisible();
  const mobileBounds = await shield.boundingBox();
  expect(mobileBounds.width).toBe(mobileBounds.height);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: '../data/reports/etapa-6/identidad-mobile.png', fullPage: true });
});
