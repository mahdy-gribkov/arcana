# TypeScript review checklist (judgment only)

Run the project gates first (`../SKILL.md`). Everything tsc, ESLint, knip or another gate reports is settled by the tool; this list covers
what a tool cannot decide. Each rule carries its reason and a source, so it teaches instead of dictating. Tags: **[tool]** a tool enforces
it when the recommended baseline in `typescript-strict.md` is on; **[judgment]** no tool decides it.

## Contents
1. Outcome and the leaner option
2. Delete what this makes dead
3. Reuse
4. Layers must pay
5. Types
6. Errors
7. Names
8. Boundaries and required values
9. Tests
10. Checks
11. Comments
12. Safety
13. Commit shape
14. What ran and what did not
15. Findings format

## 1. Outcome and the leaner option [judgment]

Read the ask as the outcome wanted. When the literal ask needs a new layer, name the leaner option and build that unless told otherwise.
Build nothing for a need nobody has today. Source: Fowler, Yagni (martinfowler.com/bliki/Yagni.html); Google review guide,
over-engineering (google.github.io/eng-practices/review/reviewer/looking-for.html).

## 2. Delete what this makes dead [judgment]

Every added layer, wrapper, copy or check names what it deletes. Never keep a second store or a second code path beside the old one:
expand, migrate, delete, in the same release train. When a new function replaces an old one, the old one goes in the same commit
(knip flags an unused export [tool]). Source: Fowler, Parallel Change (martinfowler.com/bliki/ParallelChange.html).

## 3. Reuse [judgment]

Both nearest siblings and the shared modules were read. Reuse order: the platform, the compiler and linters, an existing helper, a
library, new code. Before reusing a transformer or helper, check its contract: the input form it expects, what it loses, how it fails (a
shared email normalizer versus a hand-written `.trim().toLowerCase()`; one `escapeHtml` that drops the apostrophe and one that does not).

## 4. Layers must pay [judgment]

A package or seam needs two real users today. An abstraction names its payoff; "abstraction is good" is not one. An interface that exists
only so a test can mock it is not a payoff: prefer real implementations or small in-memory fakes. A wrapper that forwards its arguments
unchanged is a defect. Extract repeated logic at the second use, not the first. Source: Go style decisions, interfaces
(google.github.io/styleguide/go/decisions).

## 5. Types

- **[judgment]** Parse at the boundary, then trust the type. Untrusted input becomes a typed value once (zod `safeParse`), and nothing
  downstream re-checks it. Source: "Parse, don't validate" (lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/).
- **[judgment]** Make illegal states unrepresentable: a discriminated union, never boolean flags for mutually exclusive states.
- **[judgment]** Never two parameters that must agree. If `sendClass` follows from `mailKind`, derive it; do not pass both and check them.
- **[judgment]** Derive types instead of repeating them: `typeof`, `z.infer`, an ORM's inferred row type, `Pick`, `Omit`.
- **[judgment]** More than three parameters, or any boolean parameter: an options object, or two functions with honest names.
- **[tool]** No `any`, no `!`, no unsafe type assertion in production code (`no-explicit-any`, `no-non-null-assertion`,
  `no-unsafe-type-assertion`). Fix the type at its source. Prefer `satisfies` over `as`. **[judgment]** Close a union with an exhaustive
  `never` check.
- **[tool]** Explicit return types on exported functions (`explicit-module-boundary-types`).
- **[judgment]** Named exports, except where a framework requires a default export (Next.js pages and layouts).
- **[judgment]** Package aliases across packages, relative paths within one. Source: Google TypeScript guide
  (google.github.io/styleguide/tsguide.html).

## 6. Errors [judgment]

- An expected failure (invalid, not found, denied) is a value with a stable code, for example `'ok' | 'NOT_FOUND'`. An unexpected one
  throws an `Error` with `cause` and a message that says what failed, why and what to try.
- Translate a vendor error once, at the edge. Callers branch on the code, never on message text.
- No empty `catch`. No `catch` that returns a value that looks valid (`0`, `[]`, `false`) behind a gate: the error path and the genuine
  zero must differ, and the caller fails closed.
- A dependency that is down fails closed. Stored data that does not decode is treated as absent: delete it and re-derive, so one bad row
  cannot lock a user out.
- Every promise is awaited, returned, or handed to the runtime's after-response hook (`no-floating-promises` [tool]). Throw only `Error`
  objects (`only-throw-error` [tool]). Check the lint config for which of these already run.
- Sources: Go code review comments and Effective Go (error values); MDN `Error.cause`.

## 7. Names [judgment]

- A name says what the thing is or does, in domain words. Not the driver (`sendBrevoEmail`) and not an empty label (Manager, Helper,
  Util, Service, Data, Info). Survey sibling names with Grep and match the real convention.
- One concept, one name across code, database, screens and docs. Domain terms are defined once.
- No stutter (`mail.mailKind` becomes `mail.kind`). No `utils`, `helpers`, `common` or `types` drawers: name the file for its content.
- Name a regex instead of explaining it. Sources: Google TypeScript guide; Go style decisions, naming.

## 8. Boundaries and required values

- **[tool]** Dependencies point inward (`no-restricted-imports` or an import-boundary plugin). **[judgment]** The consumer defines the
  narrow type it needs. Export only what another module imports (knip **[tool]**).
- **[judgment]** One home per fact: a schema, normalizer, escaper, signer or timeout helper lives in one place. A copy found in review
  is deleted in favor of the original.
- **[judgment]** A value a caller can forget (env, config, id, limit, timeout, locale, tenant) has no default. It is required, and a
  missing value fails at the boundary (type error or startup error). A zod `.default()` or a `?? fallback` on such a value is a silent
  fallback; flag it. Absence that is a valid answer is modeled in the type.

## 9. Tests [judgment]

Tests prove behavior at the observable seam, on real implementations where practical. A test that re-proves what tsc, ESLint or a gate
proves is a finding. Deleting the line under test must fail a test (see the `testing` skill). Tests obey the same complexity bar as
code; pure functions use `it.each` tables.

## 10. Checks [judgment]

A new check passes the cheapest-first order: a type, then a compiler flag or lint rule, then a test, then a custom gate. A check that only
repeats the compiler or a linter is removed, not bent around. A custom gate carries no baseline and no hand-made escape tag. A count is
never the work item.

## 11. Comments [judgment]

Comments may be dense and may narrate. Each one is true after this change; a comment the diff makes false is a defect. Prefer the reason
itself over a ticket number or a plan id, because those rot. JSDoc on a package's exported contract. The README changes in the same
commit as the behavior.

## 12. Safety [judgment]

Guards match the sibling routes. Limits are named constants. No secret or personal data in a log. A change that stores, sends or exposes
personal data was checked against the privacy rules that apply (retention, consent, access, erasure); use `security-review` for the
security pass.

## 13. Commit shape [judgment]

One finished logical change per commit, tests with it, a refactor in its own commit, reviewable in minutes.

## 14. What ran and what did not [judgment]

List the gates that ran and the ones that did not (MISS). Never claim green on a partial run.

## 15. Findings format [judgment]

Use `review-output.md`: file:line, why, fix with effort, source. Blocking, not blocking, and outside this change.
