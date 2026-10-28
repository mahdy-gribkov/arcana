---
type: llm
---
PASS: One table-driven test with named cases run through t.Run, covering valid units, empty input and unknown input.
PASS: In the table-driven test, checks errors with errors.Is or errors.As against the sentinel errors, never by comparing error strings and never by ignoring the error. (A fuzz target that only asserts "never panics" may discard the error; that is correct.)
FAIL: Writes several separate single-case test functions, or asserts only that err is non-nil.
