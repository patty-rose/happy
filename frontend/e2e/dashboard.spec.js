import { test, expect } from '@playwright/test';

test('app loads without console errors', async ({ page }) => {
  const errors = [];
  page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
  page.on('pageerror', err => errors.push(err.message));

  await page.goto('/');
  await expect(page.locator('.prompt-input')).toBeVisible();
  expect(errors).toEqual([]);
});

test('query returns reasoning blurb and multiple widgets', async ({ page }) => {
  const errors = [];
  page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
  page.on('pageerror', err => errors.push(err.message));

  await page.goto('/');
  await page.fill('.prompt-input', 'Show me data about vacant spaces in downtown Portland');
  await page.click('.prompt-btn');

  // Section with reasoning appears
  await expect(page.locator('.section')).toBeVisible({ timeout: 45000 });
  await expect(page.locator('.section-reasoning')).not.toBeEmpty();

  // At least 2 widgets render
  const count = await page.locator('.widget').count();
  expect(count).toBeGreaterThanOrEqual(2);

  // No JS errors
  expect(errors).toEqual([]);
});
