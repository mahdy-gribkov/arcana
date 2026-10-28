---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?docker-kubernetes"'
min: 0
max: 0
arm: both
---
The docker-kubernetes skill must NOT be invoked for this request (a CI workflow with no container or cluster work is a nearby job; the Docker and Kubernetes skill covers images, compose files and cluster manifests only).
