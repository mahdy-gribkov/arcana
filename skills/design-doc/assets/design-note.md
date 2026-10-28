## Design note: {{the change, as a plain sentence}}

Status: proposed
Date: {{YYYY-MM-DD}}
Spans components: {{yes or no}}

### Problem
{{What is wrong or missing, who it hurts, and which business or journey step it serves. Why now.}}

### Evidence
{{Every load-bearing fact with its source: file:line, commit, issue number or primary-source URL with the date read. Law and third-party terms when the change stores, sends or exposes user data. Mark anything unverified as UNVERIFIED.}}

### Options considered
1. **Delete or reuse**: {{what existing code, table or package already solves this, or what we can remove instead. If nothing, say why.}}
2. **{{Option A}}**: {{what it is, what it costs, why it could win.}}
3. **{{Option B}}**: {{what it is, what it costs, why it could win.}}
4. **Do nothing**: {{what happens if we leave it.}}

### Decision
{{The chosen option and why it beats the others. Name what is deliberately not done, and what this change makes dead and deletes.}}

### Invariants
- {{A property that must hold after the change, for example "a client reads only their own rows" or "one payment request per milestone".}}
- {{Each invariant names the test, gate or constraint that holds it.}}

### Failure modes
- {{How it breaks: the input, dependency or timing, and what the user and the operator see then.}}
- {{Partial failure and retry: what is repeated, what must be idempotent.}}

### Observability
{{How we notice it is wrong in production: the log line, the metric or analytics event, the alert or monitor check, and who reads it. Never log secrets or personal data.}}

### Rollback
{{How to undo it: revert, flag, migration down path or restore. Say what data survives a rollback, or why the change is additive and needs none.}}

### Diagram
{{Only when Spans components is yes: a Markdown image link to the exported PNG, then the path of the .excalidraw source beside it.}}

### Open items
- {{Decisions or runtime proof still missing, each with who or what takes it (a follow-up change, an issue, a named person).}}
