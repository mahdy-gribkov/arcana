# Cloudflare Workers tests: real D1, KV, R2 and Durable Objects

Read this when the project deploys to Cloudflare Workers. Any module that touches the database or another binding is best proven on the
runtime that serves production: the Cloudflare Workers Vitest integration running workerd through Miniflare. Do not fake a database for
these modules: a mock that diverges from production fails silently in production.

Package names and exports in this integration have changed between releases (the pool package was renamed and the `cloudflare:test`
exports moved). Before writing the first test, read the current Cloudflare docs ("Vitest integration" under Workers testing) and the
installed package version, and copy the shape of the existing tests in the repo rather than the snippets below.

## Contents
- How the pool is wired
- Writing a workerd test
- What cannot run here
- Checklist for a new database module

## How the pool is wired

A separate config (for example `vitest.workers.config.mts`) points the pool at `wrangler.jsonc`, so bindings come from the same file as
production:

- Use a trivial test entry as `main` when the real entry imports build output that a test run does not have.
- Read the migration folder at config time and apply it in a setup file, so tests run against the real schema and never a hand-copied
  `CREATE TABLE`.
- Isolation: per-file isolation is the safe default. If you turn it off for speed, restore state per file in a setup file (reset every
  D1, KV, R2 and Durable Object, reset the mock registry, restore timers and spies) and keep the setup files in a fixed order.
- Secrets in tests are test-only values supplied by the config, so the suite runs with no local secret file and no network.
- Raise `testTimeout` only for genuinely slow setup (password hashing inside workerd); never to hide a hang.
- Module-level state in your own code (an in-memory rate limiter) leaks between files when isolation is off. List such modules in the
  reset setup, or the failure shows up as an order-dependent flake.

## Writing a workerd test

File name `<module>.workerd.test.ts`, kept out of the node run.

```ts
import { env } from 'cloudflare:test';
import { it, expect, vi } from 'vitest';

// The module reads its bindings through one accessor; binding that one seam to the real test env puts the production query on real D1.
vi.mock('../lib/cf', () => ({ getCfEnv: () => env }));

import { isDailyLimited } from '../lib/dailyCounter';

it('stops writing once the cap is reached and stores exactly the cap', async () => {
    const namespace = `daily-${crypto.randomUUID()}`;
    expect(await isDailyLimited(namespace, 2)).toBe(false);
    expect(await isDailyLimited(namespace, 2)).toBe(false);
    expect(await isDailyLimited(namespace, 2)).toBe(true);
    const row = await env.DB.prepare('SELECT count FROM daily_counters WHERE namespace = ? AND day = ?')
        .bind(namespace, new Date().toISOString().slice(0, 10)).first<{ count: number }>();
    expect(row?.count).toBe(2);               // the over-cap call wrote nothing
});
```

Rules:

1. Assert the stored state with a `SELECT` (or the KV, R2 or Durable Object read), not only the return value. A state-machine test ends on
   the final database state.
2. Give each test its own keys (`crypto.randomUUID()` in the namespace, email or id) so tests do not depend on order.
3. Seed through the same helpers production uses, or with plain `INSERT` statements.
4. Test the tenant predicate: a read or write for user A must not see user B's rows. Write one tenant-isolation test file and add each
   new tenant-scoped read to it; test a write with a second user's row left untouched.
5. A regression test sets up the exact state of the bug (see `regression-and-golden.md`) and names the bug in a comment.
6. `vi.mock` only the platform seam and genuinely external edges. Everything between the entry point and the database runs for real.
7. Use `SELF` / `fetch` on the test Worker only for tests of a Worker entry. Exercise Durable Object classes through their binding.
8. A service binding to another Worker needs an auxiliary Worker entry in the pool config; give it a stand-in that answers like an
   unconfigured Worker when you do not test it.

## What cannot run here

- The workerd pool emits no v8 coverage. Modules that only this pool can run (database modules, pages, server actions) are therefore not
  in `coverage.include`; they are proven by a workerd test or the e2e instead (see `coverage-gates.md`).
- Real network: nothing calls out. A new external call gets a double in the test, never a live request.

## Checklist for a new database module

1. The module gets its database through one seam (an accessor such as `getDb()`), so that accessor is the only thing mocked.
2. A `*.workerd.test.ts` covers: the happy path with a state assertion, each rejection path, the tenant predicate, and idempotence if
   the operation can be retried.
3. A new migration is applied in the pool automatically (the folder is read at config time); a test that needs the new column proves the
   migration, not a hand-made table.
4. Run the workers suite once for the change-set.
