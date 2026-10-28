---
type: llm
---
PASS: Does not use a direct ALTER TABLE RENAME COLUMN while old code still reads the old name.
PASS: Describes the expand and contract steps: add the new column, backfill in batches, deploy code that reads and writes both, then switch reads, then drop the old column.
PASS: Mentions keeping the two columns in sync during the transition, for example with application writes or a trigger.
FAIL: Gives a single ALTER TABLE statement as the whole answer.
