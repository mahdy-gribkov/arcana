---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---
This query takes 8 seconds on a 20 million row orders table in PostgreSQL. EXPLAIN ANALYZE shows a Seq Scan on orders. What do I do?

```sql
SELECT id, total, status
FROM orders
WHERE user_id = 4821 AND status = 'pending'
ORDER BY created_at DESC
LIMIT 20;
```
