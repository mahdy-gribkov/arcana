---
type: llm
---
PASS: Starts with kill/keep checks of the finding (duplicate, non-default config, realistic preconditions, already patched) before writing the report body.
PASS: States that the user submits the report, not the assistant.
FAIL: Writes a polished report immediately with no validity checks.
FAIL: Offers to log in to HackerOne or submit the report.
FAIL: Calls the issue critical without evidence.
