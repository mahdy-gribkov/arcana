---
name: bugbounty-report
description: Builds and verifies a bug bounty or vulnerability report before submission (HackerOne and similar) with kill-or-keep checks on the finding, the report body and PoC package in platform format, and a compliance check against the program's public policy. Use when writing, formatting or pre-submit auditing a security finding, its PoC zip or its report text, or when someone says bug bounty report, HackerOne report, vulnerability report, security disclosure, PoC package or pre-submit review. For reviewing your own code for vulnerabilities use security-review instead.
allowed-tools: Read, Glob, Grep, Bash(node ${CLAUDE_SKILL_DIR}/scripts/scan-package.mjs:*)
---

# Bug bounty report: build and verify to golden standard

Run this before any finding goes to a bounty platform. Four jobs, in order:
1. Run the invalidation gauntlet: prove the finding is real, reachable and submittable, or kill it (`references/verification.md`). A clean kill, or a downgrade to conditional or informative, is a valid result.
2. Write the report and PoC to platform format (`references/golden-format.md`).
3. Clear the compliance gates from the platform's and the program's own public policies (`references/compliance.md`).
4. Hand off field by field for the researcher to paste, verify and submit.

Never submit for the researcher. Never log into, or scrape, the researcher's bounty account or any auth-gated page. The researcher files from their own account, checks the review screen and clicks submit. Walk the hand-off one field at a time and wait for confirmation.

## HackerOne basics (static, no need to re-research)

The researcher submits a report to a program. The program's triager validates it, sets the final severity and pays by severity. A submission holds: Title (vulnerability plus asset), Weakness (CWE), Severity (CVSS vector and score), Asset (in scope), Description, Impact (its own field, concrete and bounded), Attachments (the PoC zip, often required for a bounty). Disclosure is program-controlled: hold the report confidential until the program approves. Submit through one channel only (the platform, not also a security email or GHSA).

## Operating rules

- Nothing is trusted until verified. Every source, version and behavior claim maps to a file:line, a command output or a primary-source URL.
- Platform structure is static. Program facts (scope tier, CVSS version, reward floor, signal caps, disclosure setting) and platform policies are volatile: re-verify them from current public sources on every submission and date them. A fetch that returns only a JavaScript shell is a method failure, not proof the data is private; try another public source.
- Sourcing order for a needed fact: public web, the codebase, local static notes (which can be stale), the researcher as last resort.
- Match severity to evidence: the accurate CVSS vector, no inflation, no sandbagging. The program sets the final severity.
- The PoC must reproduce from a clean state using only its own files. Test it; do not assume it.
- Voice is terse and factual (`references/golden-format.md`). No hedges, no severity adjectives, no dashes, no emojis.

## Workflow

1. Gauntlet (`references/verification.md`): run gates G0 to G9 in order. Each returns KEEP or KILL; one KILL means do not submit, and record the kill honestly in the evidence ledger.
2. Write (`references/golden-format.md`): the platform's section order, fenced code with language hints, verbatim captures, one version table, primary-source references.
3. Scan the package: extract the PoC zip into an empty folder and run `node "${CLAUDE_SKILL_DIR}/scripts/scan-package.mjs" <folder>`. It flags personal emails, secrets (values are never printed), local user paths, non-reserved endpoints, dashes and emojis, and exits 1 on any finding. Review each hit: a real production endpoint in a script is a fix; a documented URL in a README may be fine. Scan the package, not the report text, since the report legitimately cites URLs.
4. Comply (`references/compliance.md`): run the checklist, re-verify program facts, run a duplicate check against public advisories.
5. Hand off: emit the nine submission fields in order (Asset, Weakness, Severity, Title, Affected versions, Affected file permalink, Description, Impact, Attachment), each as its own copy-paste block. Wrap Description and Impact in four-backtick fences so their inner code blocks survive the paste. State the human-only gates: the researcher confirms the CVSS version and scope on the current public program page, checks the rendered review screen, attaches the zip and submits.

## Deliverables

- The report split into the platform's fields, each copy-paste ready.
- A PoC package that reproduces from clean and contains no personal data, secrets or local paths.
- A short compliance verdict: passed items, and the human-only gates the researcher must clear before submitting.
