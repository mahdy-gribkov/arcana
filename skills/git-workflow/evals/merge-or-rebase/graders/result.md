---
type: llm
---
PASS: Notes that the branch is shared with a teammate, so rewriting history is risky, and recommends merging main in (or coordinating before any rebase).
PASS: Gives concrete git commands, and if rebase is mentioned uses --force-with-lease, never a plain force push.
FAIL: Recommends rebasing and force pushing the shared branch without warning.
