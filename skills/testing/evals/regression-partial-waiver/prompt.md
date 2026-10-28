---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---
Bug: when support applies only a partial discount to an invoice, the invoice page still shows the full amount as payable. The fix is in payableCents in src/lib/invoiceSchedule.ts. Add the regression test.
