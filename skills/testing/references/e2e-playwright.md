# Playwright end-to-end tests

Generic advice that stays true everywhere: role and label locators, web-first assertions with no sleeps, one isolated context per test,
saved sign-in state, traces on retry. Run e2e against the same build you ship (a production build of the app), not the dev server, so the
test sees real bundling, caching and runtime behavior.

## Contents
- How a run works
- Config facts worth fixing
- Accounts and data
- Locators and waits
- Fixtures and sign-in state
- What every app should cover
- Mocking and the network
- Debugging a failure
- Run discipline

## How a run works

A typical script is a prepare step (build, apply migrations, wipe and seed the test accounts) followed by `playwright test`, with
Playwright's `webServer` option starting the built app and waiting on a health URL.

- Seed the data the specs need in the prepare step so a run is repeatable from an empty state.
- Keep outbound mail, payments and calendar calls captured or doubled at the server (a transport switch such as `EMAIL_TRANSPORT=capture`),
  never sent.
- Use the vendor's documented always-pass test keys for CAPTCHA widgets in test mode (Cloudflare Turnstile and reCAPTCHA both publish
  them); never disable the widget code path.
- If a port is busy, fail with the holder's name instead of killing the process.

## Config facts worth fixing

```ts
export default defineConfig({
    testDir: 'e2e',
    fullyParallel: false,            // spec FILES still run on separate workers
    workers: process.env.CI ? 2 : 3, // a cap, not a target: do not raise it to finish a flaky suite sooner
    retries: process.env.CI ? 2 : 0,
    forbidOnly: !!process.env.CI,
    timeout: 60_000,
    use: { trace: 'on-first-retry' },
    projects: [
        { name: 'setup', testMatch: /.*\.setup\.ts/ },
        { name: 'chromium', use: { storageState: 'e2e/.auth/user.json' }, dependencies: ['setup'] },
    ],
    webServer: { command: 'pnpm start', url: 'http://localhost:3000/api/health', reuseExistingServer: false },
});
```

- Retries exist to report flakiness, not to cure it. A spec that passes only on a retry is broken: read the CI run summary for the
  "flaky" count, not just the final colour.
- A spec must not depend on the machine's time zone, locale or country. Set `locale`, `timezoneId` and any geo header explicitly, and
  pre-seed a consent choice so a cookie banner never covers a click.
- Device specs run only on the phone and tablet projects they name, not on every project.

## Accounts and data

- Shared accounts are READ ONLY. A spec that changes its account (plants rows, switches language, adds a site) owns a dedicated one, and
  its sign-in state is saved by a setup project. Two specs never share a changing account, because workers would show each other
  half-done state.
- Plant and read database rows through one shared helper (a test-only endpoint, a direct connection, or the platform's local explorer),
  not through ad hoc shell commands inside specs.
- Test accounts use a reserved domain (`@e2e.test`, `@example.com`) so a wipe step can target them and never real users.
- Generate TOTP codes from a test secret in a helper; never type a real secret into a spec.

## Locators and waits

- `getByRole`, `getByLabel`, `getByText`, `getByPlaceholder`; scope inside a row (`page.getByRole('row', { name }).getByRole('button', ...)`);
  `getByTestId` only when no semantic handle exists. No CSS class selectors.

```ts
// BAD: couples the test to markup, and is ambiguous when two delete buttons exist
await page.locator('.btn-danger').click();

// GOOD: what the user perceives, scoped to the row
const row = page.getByRole('row', { name: 'Alice' });
await row.getByRole('button', { name: 'Delete' }).click();
```

- Web-first assertions (`await expect(locator).toBeVisible()`, `toHaveText`, `toHaveURL`) retry until true. Never `waitForTimeout`.
- For an absence ("nothing opens", "no request is made") and for the moment a page is ready, write one shared helper per condition
  (`untilHydrated(page)` waiting for a hydration marker, `afterAnimations(page)`) and reuse it. To jump over a page timer use the
  Playwright clock (`page.clock.install`), not a sleep.
- Extract a helper module at the second use instead of copying steps between specs. A small helper module per area beats a class-based
  page object for most suites; either is fine if the suite is consistent.
- Check layout work at 320 px and at 700 to 1024 px as well as desktop, and in each language for anything with copy. For right-to-left
  languages assert `dir="rtl"` on the surface root.

## Fixtures and sign-in state

Log in once in a setup project and reuse the saved state; do not repeat the login UI in every test.

```ts
// auth.setup.ts
import { test as setup } from '@playwright/test';

setup('sign in', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel('Email').fill(process.env.E2E_USER_EMAIL);
    await page.getByLabel('Password').fill(process.env.E2E_USER_PASSWORD);
    await page.getByRole('button', { name: 'Sign in' }).click();
    await page.waitForURL('/dashboard');
    await page.context().storageState({ path: 'e2e/.auth/user.json' });
});
```

Read credentials from the environment (required, no fallback) and keep the saved state file out of version control. Use
`test.extend` for reusable setup such as a seeded project; every test still gets its own context, so no state leaks between tests. Use
`test.describe.serial` only for a flow whose steps truly depend on each other.

## What every app should cover

- One accessibility spec per app that runs axe (`@axe-core/playwright`) on the main routes; WCAG 2.1 AA is the usual bar (see
  `accessibility-wcag`).
- A route inventory that the audits walk, so a new route is covered by the accessibility and responsive checks by default.
- A new user journey gets one spec of the whole path (the real UI against the real local backend), not a copy of a unit test.
- Visual regression (`toHaveScreenshot`) only for stable surfaces, with dynamic regions masked and baselines reviewed in the diff.

## Mocking and the network

Mock only what the local backend cannot reach and only at the browser edge (`page.route` registered BEFORE navigation, `route.fulfill` with
a typed body). Server-side doubles cover mail, calendar and similar services. Never point a spec at a production host or a real
third-party account.

```ts
await page.route('**/api/users', (route) =>
    route.fulfill({ status: 200, json: [{ id: 1, name: 'Alice' }] }),
);
await page.goto('/users');
await expect(page.getByText('Alice')).toBeVisible();
```

## Debugging a failure

Read the output already captured; the HTML report is `playwright-report/`, and the trace of a retried test is in `test-results/`. Re-run
the one spec with `npx playwright test -g "<title>"`, adding `--trace on`, `--headed` or `--debug` when needed. `npx playwright codegen`
is for finding a locator, not for pasting a recording into the suite.

## Run discipline

Run the full e2e suite once per change-set, after the unit suites are green, and read all failures from that run before fixing. Free the
test ports and end leftover server, browser and worker processes at the end of a task. E2E is a heavy run: do not run it in parallel with
other builds.
