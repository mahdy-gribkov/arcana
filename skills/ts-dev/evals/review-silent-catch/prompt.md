---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---
Review this TypeScript before I commit it:

```ts
export async function loadQuota(db: Database, userId: string, limit = 50) {
  try {
    const row = await db.get(userId);
    return (row as any).used! < limit ? 0 : row.used;
  } catch (e) {
    return 0;
  }
}
```
