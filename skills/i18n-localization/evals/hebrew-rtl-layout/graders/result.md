---
type: llm
---
PASS: Sets lang and dir=rtl on html from the active locale.
PASS: Converts the physical left and right properties to logical ones (inline-start, inline-end, margin-inline, text-align start).
FAIL: Only adds a one-off [dir=rtl] override for each rule and keeps the physical properties.
