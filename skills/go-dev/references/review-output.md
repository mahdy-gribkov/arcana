# How to write up a Go review

Lead with the `go-check` result line, then judgment findings only. Never re-report what a linter already reports; the tool output is the
finding. Order by consequence, not by file.

Each finding, one block:

```
**<file>:<line>** <rule, in five words or fewer>
Why: <the consequence for a consumer or an operator, one sentence>
Fix: <the concrete change, one sentence; a code line when it is shorter than prose> (effort: <minutes>)
Source: <the checklist rule or the cited style guide>
```

Then two short lists:

- **Not blocking** (preferences such as receiver names or wording): raise once, do not repeat per occurrence.
- **Outside this change** (a problem found nearby that has a separate cause): name it, say where it is fixed, and put it in the plan or an
  issue that names the layer which picks it up. A problem found is still worth fixing; "outside this change" only means a different commit.

Close with one line: merge as is / merge after the blocking fixes / needs another round.
