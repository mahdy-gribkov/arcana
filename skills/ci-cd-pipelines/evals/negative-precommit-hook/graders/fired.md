---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?ci-cd-pipelines"'
min: 0
max: 0
arm: both
---
The ci-cd-pipelines skill must NOT be invoked for this request (a local git hook is a nearby job; the CI/CD skill covers hosted pipelines such as GitHub Actions and GitLab CI only).
