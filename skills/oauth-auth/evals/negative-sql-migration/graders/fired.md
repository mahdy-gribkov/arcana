---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?oauth-auth"'
min: 0
max: 0
arm: both
---
The oauth-auth skill must NOT be invoked for this request (a schema migration is a nearby job; the OAuth and authentication skill covers sign-in flows, tokens and sessions only).
