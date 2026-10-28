---
type: llm
---
PASS: One table-driven test with named cases run through t.Run, covering valid units, empty input and unknown input.
PASS: Checks errors with errors.Is or errors.As against a sentinel or typed error, never by comparing error strings, and never discards an error with the blank identifier.
FAIL: Writes several separate single-case test functions, or asserts only that err is non-nil.
