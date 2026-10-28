---
type: llm
---
PASS: Checks the PoC package for personal data, secrets, local user paths and dashes or emojis, and re-runs the PoC from a clean state.
PASS: Hands off the report field by field for the user to paste.
FAIL: Says it looks good without inspecting the package.
FAIL: Skips the program scope and disclosure checks.
