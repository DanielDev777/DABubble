import { execFileSync } from 'node:child_process';

import { expect, Page, test } from '@playwright/test';

/**
 * Part 9b end to end: the two flows that span both ends of the stack.
 *
 * Needs the compose stack up (`docker compose up -d`) — the same precondition
 * as session.spec.ts, plus `docker` on PATH for reading the console-backend
 * mail out of the web container's log.
 */

const PASSWORD = 'e2e-pass-4711';

/**
 * app-text-field passes `placeholder` down to its inner <input>, and Angular
 * also leaves the static attribute on the host element — so a bare
 * getByPlaceholder() matches both. Ask for the input explicitly.
 */
function field(page: Page, placeholder: string) {
  return page.locator(`input[placeholder="${placeholder}"]`);
}

function unique(prefix: string): string {
  return `e2e-${prefix}-${Date.now()}@example.com`;
}

function compose(...args: string[]): string {
  return execFileSync('docker', ['compose', ...args], {
    cwd: '..',
    encoding: 'utf8',
    maxBuffer: 32 * 1024 * 1024,
  });
}

/** Signs up through the UI and stops on the avatar step. */
async function signUp(page: Page, email: string, name = 'Ada Lovelace'): Promise<void> {
  await page.goto('/signup');
  await field(page, 'Name und Nachname').fill(name);
  await field(page, 'beispielname@email.com').fill(email);
  await field(page, 'Passwort').fill(PASSWORD);
  await page.getByRole('checkbox').check();
  await page.getByTestId('signup').click();
  await expect(page).toHaveURL(/\/avatar$/);
}

/**
 * The console email backend prints the whole message to stdout, so the link the
 * user would click is in the web service's log. Scraping it (rather than minting
 * a token in a shell) is the only way to catch a reset-password path that no
 * longer matches what make_reset_link writes into the mail.
 *
 * Anchored on the recipient rather than a timestamp: the host clock and the
 * Docker VM clock drift by about a second, which is enough for `logs --since`
 * to filter out the very message we just triggered.
 */
async function resetLinkFor(email: string): Promise<string> {
  let link = '';

  await expect
    .poll(
      () => {
        const log = compose('logs', 'web');
        const start = log.lastIndexOf(`To: ${email}`);
        if (start === -1) return false;

        const match = /https?:\/\/\S*\/reset-password\?uid=\S+/.exec(log.slice(start));
        if (!match) return false;

        link = match[0];
        return true;
      },
      { message: `no reset link for ${email} in the web log`, timeout: 15_000 },
    )
    .toBe(true);

  return link;
}

test.afterAll(() => {
  // Every run leaves real accounts behind; the emails are namespaced so this
  // cannot touch anything a human created.
  compose(
    'exec',
    '-T',
    'web',
    'python',
    'manage.py',
    'shell',
    '-c',
    "from django.contrib.auth import get_user_model;"
      + "print(get_user_model().objects.filter(email__startswith='e2e-').delete())",
  );
});

test('signup through avatar lands in the workspace', async ({ page }) => {
  await signUp(page, unique('signup'));

  await page.getByTestId('avatar-bob').click();
  // The first authenticated write in the app: this is where X-CSRFToken meets a
  // CSRF-enforcing Django endpoint. A 403 here means withXsrfConfiguration.
  await page.getByTestId('avatar-continue').click();

  await expect(page).toHaveURL(/\/workspace$/);
  await expect(page.getByTestId('current-user')).toHaveText('Ada Lovelace');

  await page.reload();
  await expect(page).toHaveURL(/\/workspace$/);
});

test('a rejected password does not burn the reset link', async ({ page }) => {
  const email = unique('reset');
  await signUp(page, email);
  await page.getByTestId('avatar-quiff').click();
  await page.getByTestId('avatar-continue').click();
  await expect(page).toHaveURL(/\/workspace$/);
  await page.getByTestId('logout').click();
  // Wait for the logout to land: /passwort-vergessen is behind guestGuard, and
  // navigating while the session is still live bounces straight back.
  await expect(page).toHaveURL(/\/login$/);

  await page.goto('/passwort-vergessen');
  await field(page, 'beispielname@email.com').fill(email);
  await page.getByTestId('send-reset').click();
  await expect(page).toHaveURL(/\/login$/);

  // Follow the link's path on the app's own origin: the mail carries whatever
  // FRONTEND_URL says, which need not be the host Playwright is driving.
  const link = new URL(await resetLinkFor(email));
  await page.goto(link.pathname + link.search);

  // A password Django's validators reject must fail without consuming the
  // token — the 8c ordering property, and the reason this is an E2E.
  await field(page, 'Neues Passwort').fill('password1234');
  await field(page, 'Passwort bestätigen').fill('password1234');
  await page.getByTestId('reset-submit').click();
  await expect(page.getByTestId('link-error')).toHaveCount(0);
  await expect(page.getByRole('alert')).toContainText('häufig');

  const strong = 'k0rrekt-pferd-batterie';
  await field(page, 'Neues Passwort').fill(strong);
  await field(page, 'Passwort bestätigen').fill(strong);
  await page.getByTestId('reset-submit').click();
  await expect(page).toHaveURL(/\/login$/);

  await field(page, 'beispielname@email.com').fill(email);
  await field(page, 'Passwort').fill(strong);
  await page.getByTestId('login').click();
  await expect(page).toHaveURL(/\/workspace$/);
});
