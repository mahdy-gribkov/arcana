# Golden-standard and regression tests: the how-to

The contract: every test must be able to catch a real regression. This file is the method for meeting it and for proving it.

## Contents
- The mutation check
- Writing the regression test
- Weak assertions and their replacements
- State machines and money
- Reviewing a test (new or existing)

## The mutation check

A passing test proves nothing until you have seen it fail for the right reason. After a test is green, break the code under test in the
smallest way that changes the behavior it claims to protect, and run that one test file:

1. Pick the mutation: delete the line the test is about, flip the comparison (`<` to `<=`), return the old value, remove the guard, drop the
   user-id predicate from a query, swap an argument.
2. Run only that test file (the single-file run is for this check; the full suite still runs once per change-set at the end).
3. Expect a red test whose failure message names the behavior. A test that stays green, or fails for an unrelated reason (a typo, a missing
   import), is not golden: strengthen its assertion or its setup.
4. Undo exactly the one-line mutation by hand. Do not use a blanket `git checkout` or `git stash` that could drop the real change.
5. Repeat for each branch the test claims to cover (a handful per file is enough, not every line).

For a bug fix the mutation is the fix itself: revert only the fix line and the regression test must go red; restore the fix and it goes
green. Say in the report that you proved it ("fails without the fix on line N, passes with it").

## Writing the regression test

The protocol has four steps: build the exact state of the bug, run the broken path, assert the corrected behavior with a comment naming
the bug, and confirm the test would have failed before the fix. In practice:

- Use real values for the state (the row, the account shape, the flag combination, the locale), not a simplified stand-in, and enter through
  the real entry (the action, the route handler, the function the page calls), not a helper nearby.
- Put the test in the layer where the code runs: pure logic in node, a control in DOM, a database path against a real database or the
  Workers pool, a journey in e2e, beside the code's other tests (same file when it fits).
- Prove it red without the fix and green with it (the mutation check above), and say so in the report.

```ts
// Regression: a partial discount still showed the full amount as payable on the invoice page.
it('shows the reduced amount when support applies only part of a discount', () => {
    const invoice = invoiceRow({ amountCents: 400_000, discountCents: 75_000 });
    expect(payableCents(invoice)).toBe(325_000);
});
```

## Weak assertions and their replacements

| Weak | Replace with |
| --- | --- |
| `expect(fn).toHaveBeenCalled()` | `toHaveBeenCalledTimes(1)` plus `toHaveBeenCalledWith({ exact payload })` |
| `expect(x).toBeTruthy()` / `toBeFalsy()` (lint error with the recommended rules) | `toBe(expected)`, `toEqual(...)`, `toContain(...)` |
| `expect(element).toBeInTheDocument()` alone | the role, name and state: `getByRole('button', { name }).toBeDisabled()`, the text content, the attribute |
| `expect(list).toHaveLength(3)` on markup | assert the visible behavior or the specific items |
| `expect(result).toBeDefined()` alone | the value, or a guard followed by value assertions |
| a snapshot of a component | assertions on the behavior the snapshot was hiding |
| asserting a mock returned what the mock was told to return | assert what the code under test did with it |
| `if (x) { expect(...) }` (lint error) | restructure so the assertion always runs |

## State machines and money

- A test of a transition ends on the stored state after the transition (read the row), and also tests the transitions that must be refused,
  leaving the state unchanged.
- Money is integer minor units (cents). Assert exact integers, include rounding boundaries and any tax line, and test that a partial
  discount, a refund and a rate change do not alter an unrelated payment.
- Idempotent operations (webhooks, retried actions, conditional claims) are called twice in the test and the second call asserts no second
  side effect (no second row, no second mail).
- Permissions: for each operation, one test as the allowed role and one as a role that must be refused, plus the cross-user case (user A
  cannot read or change user B's rows).

## Reviewing a test (new or existing)

Read the test, not the coverage number. Ask: what behavior does this protect, which line of production code could I delete without it
failing, does it set up the real state or a convenient one, does it assert the outcome or only that something ran, does the mock match the
current implementation. Report each weak test with its file and line and the stronger assertion; do not approve a test you have not seen fail.
