---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---
I inherited a Go service with a Postgres database and I must decide whether it is ready for production next week. I have the repo checked out. How should I audit it, and what should the report look like? Here is the top level:

```
cmd/server/main.go
internal/handlers/ (14 files)
internal/db/ (raw SQL strings built with fmt.Sprintf)
migrations/ (6 files, no down migrations)
config/auth.go (contains a JWT secret literal)
tests/ (2 files)
```
