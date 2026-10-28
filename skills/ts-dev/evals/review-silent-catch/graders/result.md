---
type: llm
---
PASS: Flags the catch that returns 0, because the error path looks like a valid answer and a caller cannot tell a failure from a real zero.
PASS: Flags the any cast and the non-null assertion and asks for a typed, parsed row instead.
PASS: Flags the default value on limit as a silent fallback and asks for it to be required.
FAIL: Approves the function or only comments on formatting.
