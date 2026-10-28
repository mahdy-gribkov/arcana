# Node unit tests and DOM tests (vitest)

The contract is in `../SKILL.md`; the assertion and mutation methods are in `regression-and-golden.md`. This file is the how-to for vitest
with Testing Library. Jest users: the same shapes apply with `jest.mock` for `vi.mock`.

## Contents
- The suites and where a test goes
- Node unit tests
- DOM tests
- Mocking at the right seam
- Assertions the lint rules accept
- Time, randomness and flake

## The suites and where a test goes

| Kind | File name | Environment |
| --- | --- | --- |
| Pure logic (zod schemas, formatting, i18n, guards, crypto, route handlers with mocked seams) | `*.test.ts` or `*.test.tsx`, or in `__tests__/` | node |
| Component or hook with logic | `*.dom.test.tsx`, first line `// @vitest-environment jsdom` | jsdom |
| Code that touches Cloudflare bindings | `*.workerd.test.ts` | Workers pool (see `cloudflare-workers.md`) |
| A user journey on the built app | `e2e/*.spec.ts` | Playwright, real Chromium (see `e2e-playwright.md`) |

Exclude `*.workerd.test.ts` from the node run (`exclude: ['src/**/*.workerd.test.ts']`). Put a test where the code under test runs in
production: database code against a real database, never in a node test with a fake one.

Keep one vitest config per package, with `environment: 'node'` as the default and jsdom opted into per file by the docblock. If the
project has a shared setup file or a shared test-timeout constant, reuse it instead of repeating numbers.

## Node unit tests

- Table-test pure functions with `it.each` and a name per row. Test the boundary values the code branches on, because branch coverage
  depends on them.
- Route handlers are measured in the node suite: mock the seams (the environment accessor, the rate limiter, the session) and assert each
  guard in turn (missing origin, wrong role, rate limited, body too large, bad input, success), then assert the response status and body.
- Copy and translation modules are `Record<Locale, T>`: add a parity test that walks every locale and fails when a key is missing in one,
  so a new module cannot ship half translated.
- A server module that imports `server-only` or `next/headers` is tested with an alias that swaps `server-only` for an empty stub and
  `vi.mock('next/headers', ...)`.

## DOM tests

```tsx
// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';

const hoisted = vi.hoisted(() => ({ applyDiscount: vi.fn() }));
vi.mock('../invoiceActions', () => ({ applyDiscountAction: hoisted.applyDiscount }));

afterEach(cleanup);

it('sends the discount in cents after the user confirms', async () => {
    hoisted.applyDiscount.mockResolvedValue('ok');
    render(<DiscountForm locale="en" invoice={invoice} />);
    fireEvent.click(screen.getByRole('button', { name: copy.en.applyDiscount }));
    await waitFor(() => expect(hoisted.applyDiscount).toHaveBeenCalledTimes(1));
    expect(hoisted.applyDiscount).toHaveBeenCalledWith({ invoiceId: 'inv-1', discountCents: 32_500 });
});
```

- Wrap in the same providers production uses (a notice or toast provider, a theme provider) through one shared test wrapper, not a copy
  per test.
- Use the real translation dictionary (for example `en` and a second language) so a copy change that breaks a control breaks its test.
- Replace the server action with a spy through `vi.hoisted` plus `vi.mock`, and assert the exact payload and `toHaveBeenCalledTimes(1)`.
- jsdom has no `showModal` on `<dialog>`: stub `HTMLDialogElement.prototype.showModal` and `close` in `beforeEach` when a modal is in
  play. Stub `matchMedia` in one shared helper when a component reads media queries.
- Query by role, label or visible text, never by class or markup count. Wait for the user-visible state with `waitFor` or `findBy`. A test
  that waits on the wrong thing is fixed by waiting on the right one, not by a longer timeout.
- A DOM test proves behavior. Do not snapshot a component or add a jsdom render to lift a number: a component joins the coverage set
  only when its logic is tested to the threshold.
- A control that runs a server action is tested for: the pending state, each result code's notice, the thrown-action fallback, and that
  it does not trigger a needless full refresh.

## Mocking at the right seam

- Mock what you do not own or cannot run: the server action module a component imports, `next/navigation`, `next/headers`, the platform
  environment accessor, a third-party HTTP API. Do not mock the module under test, the database in a state test, or a pure helper.
- When the code under test makes N sequential calls, mock all N (a missing mock returns `undefined` and the test passes on wrong behavior).
- When you refactor a mocked module, update the mock to the new shape in the same change. A stale mock that still "passes" is a defect.
- `vi.restoreAllMocks()` and timer restoration belong in `afterEach` of a node or DOM suite (or in `restoreMocks: true` in the config).

## Assertions the lint rules accept

`@vitest/eslint-plugin` is worth turning on for test files: `expect-expect` (every test asserts; `assert*` helpers count), `valid-expect`,
`no-standalone-expect`, `no-conditional-expect` (an `expect` reached only inside `if` or `try` is a test that can silently assert nothing),
and `no-restricted-matchers` (ban `toBeTruthy` and `toBeFalsy`: assert the value with `toBe`, `toEqual`, `toContain`). `toBeDefined` is
acceptable only as a guard before further assertions. `!` is fine in tests (`mock.calls[0]![0]`); do not replace it with `?`.

## Time, randomness and flake

- Inject a clock or use `vi.useFakeTimers()` and restore it; never `setTimeout` or a sleep to wait for work, and never `Date.now()` in the
  expectation. Use a unique id per test (`crypto.randomUUID()`) instead of a shared name.
- A test that passes alone and fails beside others shares state: find the shared module-level state, do not add `--no-file-parallelism`.
- CI machines are slower than a developer laptop, and retries can hide a flaky spec: read the run summary. The fix is always a wait on
  user-visible state, never a delay.
