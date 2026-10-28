---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---
Our signup form fails the axe audit. Fix it so it passes WCAG 2.2 AA.

```html
<form>
  <input type="text" placeholder="Email">
  <input type="password" placeholder="Password">
  <select><option>Choose a country...</option><option>Israel</option></select>
  <div class="error" style="color:red">Invalid email</div>
  <img src="logo.png">
  <button><img src="arrow.svg"></button>
</form>
```
