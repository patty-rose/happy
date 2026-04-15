import { test, expect } from '@playwright/test';

test('app loads without console errors', async ({ page }) => {
  const errors = [];
  page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
  page.on('pageerror', err => errors.push(err.message));

  await page.goto('/');
  await expect(page.locator('.prompt-input')).toBeVisible();
  expect(errors).toEqual([]);
});

test('query returns multiple widgets', async ({ page }) => {
  const errors = [];
  page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
  page.on('pageerror', err => errors.push(err.message));

  await page.goto('/');
  await page.fill('.prompt-input', 'Show me data about vacant lots in downtown Portland');
  await page.click('.prompt-btn');

  // Wait for at least 2 widgets (multi-widget response)
  await expect(page.locator('.widget').first()).toBeVisible({ timeout: 45000 });
  const count = await page.locator('.widget').count();
  expect(count).toBeGreaterThanOrEqual(2);
  await expect(page.locator('.widget').first().locator('.widget-title')).not.toBeEmpty();

  expect(errors).toEqual([]);
});
