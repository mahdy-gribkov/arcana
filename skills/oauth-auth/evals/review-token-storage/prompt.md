---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---
Review this login flow in my React app before I ship it:

```typescript
const authUrl = "https://idp.example.com/authorize?client_id=" + CLIENT_ID +
  "&redirect_uri=" + REDIRECT + "&response_type=code";
localStorage.setItem("oauth_state", Math.random().toString());
window.location.href = authUrl;

// on the callback page
const tokens = await exchangeCode(code);
localStorage.setItem("access_token", tokens.access_token);
localStorage.setItem("refresh_token", tokens.refresh_token);
```
