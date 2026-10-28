---
type: llm
---
PASS: Proposes a phased process (map structure, trace data flow, check logic and concurrency, then a remediation plan).
PASS: Calls out the evidence already visible: SQL built with Sprintf (injection risk), the hardcoded JWT secret, missing down migrations, thin tests.
PASS: Asks for findings with file and line references and a severity score or health score, with a prioritized fix list.
FAIL: Gives generic advice with no phases, scoring, or evidence requirement.
