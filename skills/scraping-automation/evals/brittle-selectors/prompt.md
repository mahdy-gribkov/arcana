---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---
This Playwright scraper breaks every time the site ships a redesign. Make the extraction more resilient.

```ts
const items = await page.locator('div.sc-a1b2c3 > span.css-9x8y7z').allTextContents();
const price = await page.locator('#root > div:nth-child(3) > div > p').textContent();
```
