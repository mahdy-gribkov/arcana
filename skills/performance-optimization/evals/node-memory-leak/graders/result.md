---
type: llm
---
PASS: Gives steps to take heap snapshots (node --inspect with Chrome DevTools, or a signal-based snapshot) and compare two snapshots.
PASS: Lists common causes such as unbounded caches or maps, event listeners that are never removed, closures holding large objects, and timers that are never cleared.
PASS: Recommends a bounded cache (for example lru-cache with max and ttl) as a fix for unbounded growth.
FAIL: Only suggests raising the container memory limit.
