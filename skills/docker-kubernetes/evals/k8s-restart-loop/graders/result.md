---
type: llm
---
PASS: Explains that a liveness probe must not check the database, because a database outage would restart healthy pods.
PASS: Moves the dependency check to a readiness probe on a separate path.
PASS: Adds a startup probe for slow starts.
PASS: Gives YAML with sensible periodSeconds and failureThreshold values.
FAIL: Only raises the liveness timeout without separating liveness from readiness.
