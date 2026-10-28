# How to write up a TypeScript review

Lead with the gate lines (PASS, FAIL, MISS), then judgment findings only. Never re-report what a tool already reports; the tool line is the
finding. Order by consequence, not by file.

Each finding, one block:

```
**<file>:<line>** <rule, in five words or fewer>
Why: <the consequence for a user, an operator or the next change, one sentence>
Fix: <the concrete change, one sentence; a code line when it is shorter than prose> (effort: <minutes>)
Source: <the checklist rule or the cited guide>
```

Then three short lists:

- **Blocking**: the findings above that must change before merge.
- **Not blocking** (preferences such as wording or ordering): raise once, do not repeat per occurrence.
- **Outside this change** (a problem found nearby that has a separate cause): name it, say where it is fixed, and put it in the plan or an
  issue that names the layer which picks it up. A problem found is still worth fixing; "outside this change" only means a different commit.

Start the review with what is good, in one or two lines. Close with one line: merge as is / merge after the blocking fixes / needs another
round. State which gates did not run (MISS), so "green" is never claimed on a partial run.
