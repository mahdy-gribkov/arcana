---
type: llm
---
PASS: Recommends cursor-based pagination for a large, fast-changing dataset.
PASS: Explains that offset pagination gets slow on large offsets and returns duplicates or gaps when rows are inserted.
PASS: Shows a request with a limit and a cursor parameter, and a response with next cursor and a has-more flag.
PASS: Says the cursor should be opaque to the client.
FAIL: Recommends page and per_page without discussing the trade-offs.
