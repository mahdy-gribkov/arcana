---
type: llm
---
PASS: Says v4 is configured in CSS and that darkMode in tailwind.config.ts is not used by default.
PASS: Gives the @custom-variant dark line that matches the .dark class, for example @custom-variant dark (&:where(.dark, .dark *));
PASS: Says the toggle must add or remove the dark class on the html element.
FAIL: Tells the user to downgrade to v3 or to rewrite every dark: class by hand.
