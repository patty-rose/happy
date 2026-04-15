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

  await expect(page.locator('.section')).toBeVisible({ timeout: 45000 });
  await expect(page.locator('.section-reasoning')).not.toBeEmpty();

  const count = await page.locator('.widget').count();
  expect(count).toBeGreaterThanOrEqual(2);
  expect(errors).toEqual([]);
});

test('save dashboard button appears after query and shows confirmation', async ({ page }) => {
  const errors = [];
  page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
  page.on('pageerror', err => errors.push(err.message));

  await page.goto('/');
  await page.fill('.prompt-input', 'Portland unemployment trends');
  await page.click('.prompt-btn');

  await expect(page.locator('.section')).toBeVisible({ timeout: 45000 });
  await expect(page.locator('button:has-text("Save dashboard")')).toBeVisible();

  await page.click('button:has-text("Save dashboard")');
  await expect(page.locator('button:has-text("Saved")')).toBeVisible({ timeout: 5000 });

  expect(errors).toEqual([]);
});
