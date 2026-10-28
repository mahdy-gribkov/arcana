---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---
I wrote src/server/dailyCap.ts in my Cloudflare Worker app. It increments a row of the daily_counters D1 table per namespace and stops writing once a cap is reached. Write the test for it.
