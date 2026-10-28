---
type: llm
---
PASS: Renames the file to proxy.ts and the exported function to proxy (or a default export).
PASS: Keeps the matcher config and the redirect behavior.
PASS: Mentions that proxy.ts runs on the Node.js runtime and that middleware.ts is deprecated.
FAIL: Keeps the file named middleware.ts or says no change is needed.
