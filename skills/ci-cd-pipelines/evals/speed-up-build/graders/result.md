---
type: llm
---
PASS: Splits lint, test and build into parallel jobs.
PASS: Adds dependency caching through setup-node cache or actions/cache keyed on the lockfile hash.
PASS: Adds concurrency with cancel-in-progress and path filters so stale or docs-only runs are skipped.
FAIL: Only suggests a bigger runner without changing the pipeline structure.
