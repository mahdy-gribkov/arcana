---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?testing"'
min: 0
max: 0
arm: both
---
The testing skill must NOT be invoked for this request (a Go test request belongs to the Go development skill; the testing skill covers TypeScript and JavaScript projects only).
