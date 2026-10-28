---
type: llm
---
PASS: Waits on the user-visible state with a web-first expect (role or label locator), not a timeout or sleep.
PASS: Checks that the spec does not share a changing account or rows with another spec (a dedicated account per spec) because workers run spec files in parallel.
PASS: Notes that CI retries hide flakiness, so the run summary must be read and the fix is not "raise retries".
FAIL: Adds page.waitForTimeout, raises retries, or raises the test timeout as the fix.
