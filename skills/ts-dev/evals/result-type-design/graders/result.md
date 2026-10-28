---
type: llm
---
PASS: Proposes expected failures (missing, name taken) as values with a stable code, for example a string union, and callers branch on the code.
PASS: Proposes that the database being down throws an Error with a cause and an actionable message, not a returned value that looks valid.
FAIL: Suggests returning a boolean, or matching on error message text.
