---
type: llm
---
PASS: Recommends a composite index that starts with user_id, with created_at DESC for the sort, or a partial index on status = 'pending'.
PASS: Recommends CREATE INDEX CONCURRENTLY so writes are not blocked in production.
PASS: Says to re-run EXPLAIN (ANALYZE, BUFFERS) afterwards to confirm an index scan.
PASS: Mentions a covering index with INCLUDE as an option.
FAIL: Only suggests adding more hardware or caching the result.
