---
type: llm
---
PASS: Explains that both p-4 and p-8 (and both backgrounds) are present and CSS source order decides the winner, not the order in the string.
PASS: Recommends a cn() helper that combines clsx and tailwind-merge so the last conflicting class wins.
PASS: Also fixes the literal string undefined that appears when className is not passed.
FAIL: Suggests !important or inline styles as the fix.
