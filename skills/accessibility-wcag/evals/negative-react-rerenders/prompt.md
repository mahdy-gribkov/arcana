---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---
This React component re-renders too often when the parent state changes. Optimize it with memoization and tell me which hooks to change.

```tsx
export function Table({ rows, onSelect }) {
  const sorted = rows.sort((a, b) => a.name.localeCompare(b.name));
  return sorted.map((row) => <Row key={row.id} row={row} onSelect={() => onSelect(row.id)} />);
}
```
