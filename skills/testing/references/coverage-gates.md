# Coverage thresholds and what the include list means

Coverage finds code no test reaches; it does not prove a test asserts anything (see `regression-and-golden.md`). Layer it: a high
threshold (100 on lines, branches, functions and statements is the recommended bar for the pure-logic layer) on an explicit measured set,
never one global number diluted by generated code and glue.

## Contents
- What a gate measures
- Include semantics
- Excludes and the runtime gap
- Ignoring a line honestly
- Reading a miss
- Checking the gate itself

## What a gate measures

A gate measures exactly its `coverage.include` list in that package's vitest config, with a `thresholds` block for the four metrics:

```ts
test: {
    coverage: {
        provider: 'v8',
        include: ['src/lib/**/*.ts', 'src/app/api/**/route.ts'],
        exclude: ['**/*.test.ts', '**/*.d.ts'],
        thresholds: { lines: 100, branches: 100, functions: 100, statements: 100 },
    },
},
```

- Whole-folder globs suit the pure logic layer (`src/lib/**/*.ts`): every file in the folder is held at the threshold, so a new file
  there needs a full test immediately.
- Everything else is an explicit path, never a folder glob, and a file joins only once it is at the threshold: route handlers (with
  their guards: rate limit, origin, auth, body cap), client components and helpers that contain logic (proven by DOM tests), middleware.
- In a path, glob syntax treats parentheses and brackets specially, so a Next.js route group `(client)` or a segment `[id]` is matched
  with a single `*`: `src/app/*/projects/*/PaymentSchedule.tsx`.

## Include semantics

- To bring a file under the gate: write its tests to the threshold, then add the explicit path to `include` in the same change.
- Vitest coverage cannot include files above the package root. A package that needs a gate has its own config and its own coverage
  script.
- Pages, server actions and database modules often cannot be measured by v8 when they only run in a special runtime (for example the
  Workers pool, which emits no v8 coverage). That is a property of the tool, not a licence to skip tests: they are proven by a runtime
  test or an e2e spec instead (see `cloudflare-workers.md`).

## Excludes and the runtime gap

A `coverage.exclude` entry names the suite that actually runs the file and why, for example: `src/lib/edgeCache.ts` with the comment
"Cache API bound: edgeCache.workerd.test.ts runs it on the real runtime". An exclude without its runner and a reason is a hidden gap; do
not add one to make a number pass.

## Ignoring a line honestly

An isolated `/* v8 ignore next */` (or a block) is allowed only for code that cannot be reached by a test: a fallback the types force, a
`noUncheckedIndexedAccess` guard, a comparator equality case that a stable sort makes inert. Each carries a comment that says why it is
unreachable. A bare ignore, an ignore over reachable branches, or an ignore added after a test failed to reach a branch is a lowered gate.
If you cannot say why a line is unreachable, write the test.

## Reading a miss

1. Run the package coverage once. Do not re-run it to look at one file.
2. Read the uncovered lines and branches of the file in the captured report (the `Uncovered Line #s` column).
3. For a branch miss, write the case that takes the other side of the `if`, `?:`, `??`, `?.` or `switch` arm, with an assertion on the
   different result. A test that merely executes the line to turn the number green is filler.
4. Run once more to confirm the threshold.
5. A drop of 0.1 on a metric is a finding in your change, not a threshold problem: fix the tests, never the threshold.

## Checking the gate itself

A threshold only protects code that is in the measured set. A small script or CI step can fail the build when a package that ships source
has no `thresholds` block, or when a server module is neither measured, nor imported by some test, nor listed in an allow-list with a
reason. The allow-list may only shrink. Add such a check once the project has more than a few packages; a mock of a module does not count
as testing it.
