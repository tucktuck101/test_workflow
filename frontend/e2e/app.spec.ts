import { test, expect } from '@playwright/test';

const apiBase = process.env.E2E_API_URL || 'http://localhost:8000';

async function waitReady(page) {
  for (let i = 0; i < 10; i++) {
    const res = await page.request.get(`${apiBase}/health/ready`);
    if (res.ok()) return;
    await page.waitForTimeout(500);
  }
  throw new Error('backend not ready');
}

test('start game flow works', async ({ page }) => {
  await waitReady(page);
  await page.goto('/');
  await expect(page.getByRole('button', { name: /start/i })).toBeVisible();
  await page.getByRole('button', { name: /start/i }).click();
  await expect(page.getByText(/Game started/i)).toBeVisible();
  await page.getByRole('button', { name: /cell 0,0/i }).first().click();
  await expect(page.getByText(/Agent fired/)).toBeVisible();
});
