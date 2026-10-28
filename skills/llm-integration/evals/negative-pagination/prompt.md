---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---
Add cursor-based pagination to this REST endpoint and keep it backward compatible with the old page and limit parameters.

```ts
app.get('/api/orders', async (req, res) => {
  const { page = 1, limit = 20 } = req.query;
  res.json(await db.orders.find().skip((page - 1) * limit).limit(+limit));
});
```
