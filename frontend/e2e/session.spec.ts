import { expect, test } from '@playwright/test';

/**
 * The point of Part 9a: a real session against the real backend, through the
 * dev proxy, surviving a reload. Everything else in 9a is scaffolding for this.
 */
test.describe('session', () => {
  test('sends a signed-out visitor to login', async ({ page }) => {
    await page.goto('/workspace');
    await expect(page).toHaveURL(/\/login\?returnUrl=%2Fworkspace$/);
  });

  test('guest login survives a reload', async ({ page }) => {
    await page.goto('/login');
    await page.getByTestId('guest-login').click();

    await expect(page).toHaveURL(/\/workspace$/);
    await expect(page.getByTestId('current-user')).toHaveText('Guest');

    // The cookies are httpOnly, so staying logged in here proves the whole
    // chain: proxy, cookie JWT, restore() and the app initializer ordering.
    await page.reload();
    await expect(page).toHaveURL(/\/workspace$/);
    await expect(page.getByTestId('current-user')).toHaveText('Guest');
  });

  test('keeps a signed-in user out of the login screen', async ({ page }) => {
    await page.goto('/login');
    await page.getByTestId('guest-login').click();
    await expect(page).toHaveURL(/\/workspace$/);

    await page.goto('/login');
    await expect(page).toHaveURL(/\/workspace$/);
  });

  test('logout returns to login and locks the workspace again', async ({ page }) => {
    await page.goto('/login');
    await page.getByTestId('guest-login').click();
    await expect(page).toHaveURL(/\/workspace$/);

    await page.getByTestId('logout').click();
    await expect(page).toHaveURL(/\/login$/);

    await page.goto('/workspace');
    await expect(page).toHaveURL(/\/login\?returnUrl=%2Fworkspace$/);
  });
});
