---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---
My API pod keeps restarting every few minutes. The liveness probe calls /health, and /health runs a SELECT 1 against Postgres. Write a better probe setup for the Deployment.
