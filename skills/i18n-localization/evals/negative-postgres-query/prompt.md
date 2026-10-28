---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---
This Postgres query takes 12 seconds on a 5 million row table. Help me find out why and speed it up.

```sql
SELECT * FROM orders o JOIN customers c ON c.id = o.customer_id
WHERE LOWER(c.email) = 'a@example.com' ORDER BY o.created_at DESC;
```
