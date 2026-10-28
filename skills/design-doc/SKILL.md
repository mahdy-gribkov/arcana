---
name: design-doc
description: Writes the design note a non-trivial change needs before code (problem, evidence, options weighed, decision and why, invariants, failure modes, observability, rollback) and, when the change spans apps, packages or services, builds a high-level design diagram or a step-by-step HLD with a defect-checked Excalidraw builder. Use when asked for a design note, design doc, technical spec, HLD, high-level design, architecture diagram, component diagram, flow diagram or "how should we build this", or before adding a new table, route, package, seam, third-party service, or a payment, auth or data-boundary change.
allowed-tools: Read, Glob, Grep, Write, Edit, Bash(node ${CLAUDE_SKILL_DIR}/scripts/check-design-note.mjs:*), Bash(python ${CLAUDE_SKILL_DIR}/scripts/build_hld.py:*), Bash(python ${CLAUDE_SKILL_DIR}/scripts/smooth_scene.py:*), Bash(python ${CLAUDE_SKILL_DIR}/scripts/export_scene.py:*)
---

# Design doc

A design note makes the decision reviewable before code exists. A decision reached mid-build is a planning miss, so the note is finished, and checked, first.

## When a note is required

Write one only for a new table, route, package, seam or gate, a new third-party service, or a payment, auth or data-boundary change. Work that merely touches more than one app or package needs no note. A copy fix, a styling tweak, a local bug fix and a change inside an existing module need none.

## 1. Pin the scope

State these five lines to the requester before researching:

1. SCOPE: what is built, in one sentence, at full depth (not a reduced version).
2. BUSINESS INTENT: the user journey or business step it serves, and for whom.
3. SYSTEMIC IMPACT: other apps, entities, shared primitives, quotas and the security posture it touches.
4. EVIDENCE: what you will read and cite.
5. VERIFICATION: the gate, test or manual check that will prove it works.

If an answer is "not sure", resolve it first by asking one sharp question or reading more code. For a fuzzy idea, write the requirements first (`references/specs-and-lighter-docs.md`).

## 2. Evidence first

Read `references/evidence.md`. In short: read the real code and primary sources before asserting, cite `file:line` plus the commit sha you read, and label every behavior `current`, `proposed` or `untested`. A change that stores, sends, signs or exposes user data starts with the applicable law and the terms and free-tier limits of each third party, because they can change the question itself. Flag wording that needs a lawyer; never invent a compliance claim.

## 3. Write the note

Copy `assets/design-note.md` into the plan file or the README that sits next to the code, as a `Design note:` section. Fill every section with substance:

- **Options considered**: at least two real options, always including "delete or reuse" (what existing code, table or package already solves this, or what can be removed instead), plus "do nothing".
- **Decision**: the choice and the reason it beats the others; what is deliberately not done.
- **Invariants**: each names the test, gate or constraint that holds it.
- **Failure modes, Observability, Rollback**: concrete, with who sees what. No secrets or personal data in logs.

Set `Spans components: yes` when the change crosses apps, packages or services. That requires a Diagram section.

## 4. Diagram (only when it spans components)

Read `references/diagram-guide.md` first and pin altitude and scope before drawing: a component sketch, a subsystem view or a full HLD. Build the diagram with a short generator script that imports `scripts/excalidraw_lib.py`. `check()` raises on overlapping boxes, arrows through nodes, labels on the wrong box and text that would overflow, so a diagram that passes is legible before anyone opens it. The palette is a neutral light default (dark ink, light gray fills, one accent) defined as constants at the top of the library; edit them to match your brand. There is no dark variant. For one small flow or a data model, a Mermaid block is enough (`references/specs-and-lighter-docs.md`).

Make a PNG for the README with `scripts/smooth_scene.py` then `scripts/export_scene.py` (needs Pillow and an Arial-style font):

```
python ${CLAUDE_SKILL_DIR}/scripts/smooth_scene.py overview.excalidraw
python ${CLAUDE_SKILL_DIR}/scripts/export_scene.py overview.excalidraw overview.png
```

Keep the `.excalidraw` source and the PNG beside the README that holds the note, and link both in the Diagram section. Keep the scene inside the 1300 by 1040 canvas.

## 5. Step-by-step HLD (integration flows only)

When one design has several entrypoints (a webhook, a poll, a user action) and concrete API calls, trace each step on the same base diagram with a focus image. Write a manifest per `references/hld-manifest.md` (start from `assets/manifest.example.json`), then:

```
python ${CLAUDE_SKILL_DIR}/scripts/build_hld.py hld.json --validate-source
python ${CLAUDE_SKILL_DIR}/scripts/build_hld.py hld.json --annotate
python ${CLAUDE_SKILL_DIR}/scripts/build_hld.py hld.json --output <output dir>
```

`hld.md` is the note body to paste into the plan or README; `hld.html` is a standalone preview to review. Validation fails on stale focus images, unknown targets or routes, unused routes and missing evidence. Fix the manifest and rerun; never edit generated files.

## 6. Check and report

```
node ${CLAUDE_SKILL_DIR}/scripts/check-design-note.mjs <plan or README>
```

Fix every ERROR and read every WARN. Then report: where the note lives, the decision in one line, the check result, and what is still `untested` or open. Do not start the build in the same step unless asked; the note is the deliverable.

## Neighbouring jobs

Requirements and acceptance criteria, task breakdown after the decision, OpenAPI docs and Mermaid diagrams are in `references/specs-and-lighter-docs.md`. A bug report or issue is not a design note.
