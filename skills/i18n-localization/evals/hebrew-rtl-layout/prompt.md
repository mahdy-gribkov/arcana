---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---
We are adding Hebrew to our Next.js app. The layout is built for English. What do I need to change in the root layout and in the CSS?

```css
.sidebar { float: left; margin-right: 24px; padding-left: 16px; text-align: left; }
```
```tsx
<html lang="en">
```
