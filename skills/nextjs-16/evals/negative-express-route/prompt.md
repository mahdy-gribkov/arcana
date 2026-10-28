---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---
Add a rate limit of 100 requests per minute per IP to this Express route and show me the change.

```js
const express = require('express');
const app = express();

app.get('/api/items', async (req, res) => {
  res.json(await db.items.findAll());
});

app.listen(3000);
```
