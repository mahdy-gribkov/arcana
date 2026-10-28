---
name: testing
description: Writes, fixes and reviews tests for TypeScript and JavaScript projects, which means vitest unit and DOM tests, Playwright end-to-end specs, coverage thresholds, regression tests that reproduce the bug state, and tests of Cloudflare Workers code on real bindings. Use when adding or fixing a test, a coverage gate is red, a spec is flaky or fails in CI, a bug fix needs its regression test, a test passes but you doubt it can fail, or asked "how do we test this". Not for Go tests (go-dev), Lighthouse audits or manual QA scripts.
allowed-tools: Read, Glob, Grep, Bash(npx vitest:*), Bash(npx playwright:*), Bash(pnpm test:*), Bash(npm test:*), Bash(pnpm run:*), Bash(npm run:*)
---

# Testing TypeScript and JavaScript projects

This skill is the how-to: which kind of test, how to wire it, how to prove it can fail. If the project already has test conventions, a
runner config and sibling tests, those win over the examples here. The Go equivalent is the `go-dev` skill.

## The contract

- A test earns its place only if it can catch a real regression. Delete the line under test and a test must fail.
- Assert outcomes, not execution: concrete values, the stored state after a transition, exact call counts and payloads, the role and name
  of what the user sees.
- Mock what you do not own or cannot run (a third-party API, the clock, the framework's request context). Never mock the module under
  test, and never fake a database in a state test when a real one can run.
- A bug fix ships with a regression test that builds the bug's exact state and fails on the old code.
- Tests never touch production, real mail, real payment or real calendar accounts.

## Pick the test kind first

| The code under test | Write | Runs in | Reference |
| --- | --- | --- | --- |
| Pure logic: schemas, formatting, guards, i18n, route handlers with mocked seams | `*.test.ts[x]` | node (vitest) | `references/unit-and-dom.md` |
| A component or hook with logic, a control that calls a server action | `*.dom.test.tsx` with `// @vitest-environment jsdom` | jsdom | `references/unit-and-dom.md` |
| Cloudflare Workers code that reads or writes D1, KV, R2 or a Durable Object | `*.workerd.test.ts` | Workers vitest pool, REAL bindings | `references/cloudflare-workers.md` |
| A user journey, an a11y or layout audit | `e2e/*.spec.ts` | Playwright against a built app | `references/e2e-playwright.md` |
| A coverage threshold is red, or a file must join the measured set | tests to the threshold, then the include list | v8 | `references/coverage-gates.md` |
| A bug fix, or a test you doubt | the mutation check and the regression recipe | any | `references/regression-and-golden.md` |

Database code is tested against a real database (SQLite in memory, a container, or the platform's own test runtime), not a hand-written
fake. A component is never snapshotted to lift a number.

## Workflow

1. **Classify** the change with the table. Find the nearest sibling test (same folder) and copy its structure, setup and helpers; do not
   invent a second way.
2. **Write the behavior test first when fixing a bug.** Build the exact state of the bug, call the real entry, assert the corrected value,
   name the bug in a comment. It must go red on the old code.
3. **Assert outcomes, not execution.** Replace `toBeTruthy`, `toHaveBeenCalled()` alone and tests with no `expect` (the table in
   `references/regression-and-golden.md` lists the replacements). Lint rules from `@vitest/eslint-plugin` catch the worst of them.
4. **Prove it can fail** (the mutation check in `references/regression-and-golden.md`): break the line under test, watch the right test go
   red, undo exactly that edit.
5. **Run once.** The affected package's suite and coverage once; the integration suite when a database or binding is touched; the e2e
   suite once per change-set when a journey changed. Read all failures from that run, fix, run once more.
6. **Report what ran and what did not.** State each suite with its result, and name any suite you could not run (for example e2e without
   a free port) so green is never claimed on a partial run.

## Rules that bite

- Hold the coverage threshold the project set (100 on lines, branches, functions and statements is the recommended bar for a logic
  layer) and never lower it, exclude around it or ignore a line without a reason. See `references/coverage-gates.md`.
- Never add a delay to fix a flaky test (`setTimeout`, `waitForTimeout`, a longer timeout). Wait on the user-visible state. CI retries
  hide flakiness, so a spec that passes on retry is still broken; read the run summary, not only the final colour.
- A spec that changes its account or its rows owns them. Specs run in parallel workers, so two specs must never share a changing account.
  Do not raise the worker count to make a flaky suite finish sooner.
- Mocks follow the code. When a mocked module changes shape, update the mock in the same change; when the code makes N calls, mock N.
- A test that passes alone and fails beside others shares state: find the shared module-level state instead of turning parallelism off.

## Boundaries

A security review of guards and actions is `security-review`; accessibility rules are `accessibility-wcag` (the e2e reference covers
running axe inside a spec); page-speed scores come from Lighthouse runs, not from a unit test; building the feature itself is the
framework skill (`nextjs-16`, `api-design`); wiring the suites into CI is `ci-cd-pipelines`.
