---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---
Write a PostgreSQL migration that adds a nullable last_login_at timestamptz column to the users table and backfills it from the sessions table.
