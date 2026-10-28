---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---
Our cart says "1 items" and the Arabic translation looks broken. We use next-intl. Fix the message and the component.

```tsx
// messages/en.json: { "cart": { "count": "items" } }
const t = useTranslations('cart');
return <p>{count} {t('count')}</p>;
```
