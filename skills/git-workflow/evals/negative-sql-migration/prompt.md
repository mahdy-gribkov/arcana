---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---
Write a PostgreSQL migration that adds a nullable archived_at timestamp column to the orders table and an index for the rows where it is not null, safe to run on a live table.
