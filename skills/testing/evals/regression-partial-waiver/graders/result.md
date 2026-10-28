---
type: llm
---
PASS: Sets up the exact failing state (an invoice with a partial discount), calls payableCents, and asserts the reduced amount with a concrete value.
PASS: Names the bug in a comment and says how it proves the test fails without the fix (for example reverting the fix line and running it once).
FAIL: Only re-tests the happy path with no discount, or uses a snapshot.
FAIL: Mocks payableCents or the module under test.
