---
type: llm
---
PASS: Produces or starts a written design note with options, a decision with its reason, invariants, failure modes and a rollback plan for the migration.
PASS: Reads or asks for the real schema and code involved before deciding.
FAIL: Gives only a bulleted opinion with no options weighed and no rollback.
FAIL: Writes the migration SQL instead of the note.
