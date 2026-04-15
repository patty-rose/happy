import { test, expect } from '@playwright/test';

test('app loads without console errors', async ({ page }) => {
  const errors = [];
  page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
  page.on('pageerror', err => errors.push(err.message));

  await page.goto('/');
  await expect(page.locator('.prompt-input')).toBeVisible();
  expect(errors).toEqual([]);
});

test('prompt bar submits and renders a widget', async ({ page }) => {
  const errors = [];
  page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
  page.on('pageerror', err => errors.push(err.message));

  await page.goto('/');
  await page.fill('.prompt-input', 'Oregon unemployment rate');
  await page.click('.prompt-btn');

  // Wait for widget to appear (claude CLI + BLS fetch can take a few seconds)
  await expect(page.locator('.widget')).toBeVisible({ timeout: 30000 });
  await expect(page.locator('.widget-title')).not.toBeEmpty();

  // No JS errors during the flow
  expect(errors).toEqual([]);
});
