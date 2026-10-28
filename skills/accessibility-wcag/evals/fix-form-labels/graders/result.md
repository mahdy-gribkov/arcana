---
type: llm
---
PASS: Adds visible label elements tied to the inputs and the select with for and id.
PASS: Gives the error message a programmatic link (aria-describedby or role alert) and aria-invalid on the input, not color alone.
PASS: Adds alt text to the logo and an accessible name to the icon-only button.
FAIL: Only adds aria-label attributes everywhere without visible labels, or leaves the placeholders as the only labels.
