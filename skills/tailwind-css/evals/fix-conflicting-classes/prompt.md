---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---
My Card component ignores the classes I pass in. Why, and what is the fix?

```tsx
export function Card({ className }: { className?: string }) {
  return <div className={`p-4 rounded-lg bg-white ${className}`} />;
}

// <Card className="p-8 bg-blue-50" />
```
