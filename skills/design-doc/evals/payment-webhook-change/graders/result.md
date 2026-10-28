---
type: llm
---
PASS: Produces a design note with these parts: problem, options weighed (at least two, including doing nothing), the decision and why, invariants, failure modes, observability and rollback.
PASS: Treats a webhook that moves money status as crossing components, so it calls for a diagram or says one is needed.
PASS: Asks for or cites evidence (code, provider documentation, law for stored payment data) instead of asserting from memory.
FAIL: Starts implementing the webhook or writes code instead of the note.
FAIL: Uses an em dash or an en dash anywhere.
