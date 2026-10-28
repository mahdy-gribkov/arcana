---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---
Review this login endpoint for security problems:

```javascript
app.post("/login", async (req, res) => {
  const { email, password } = req.body;
  const rows = await db.query(
    `SELECT * FROM users WHERE email = '${email}' AND password = '${md5(password)}'`
  );
  if (rows.length === 0) return res.status(401).send("bad login");
  const token = jwt.sign({ id: rows[0].id, role: rows[0].role }, "secret123");
  res.json({ token });
});
```
