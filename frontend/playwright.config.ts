import { defineConfig, devices } from '@playwright/test';

/**
 * The app is served by the `frontend` docker service, so there is no webServer
 * block here: `docker compose up` first, then `npx playwright test`.
 *
 * Playwright runs on the host rather than in the container because the dev
 * image is node:24-alpine and Playwright ships no Alpine browser builds.
 */
export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  forbidOnly: !!process.env['CI'],
  retries: process.env['CI'] ? 2 : 0,
  workers: 1,
  reporter: 'list',
  use: {
    baseURL: 'http://localhost:4200',
    trace: 'on-first-retry',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
});
