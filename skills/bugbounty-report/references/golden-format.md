# Golden report format and voice

Source basis (read once, re-verify if platform changes): HackerOne Quality Reports
(docs.hackerone.com/en/articles/8475116-quality-reports), the h1.community triager guidance, the
reddelexc/hackerone-reports top-SSRF corpus, the bl4de community template.

## HackerOne submission fields (the form fields, in fill order)

A submission is nine form fields plus an optional Hacker summary, filled in this order (keep the source-of-truth
.md laid out with these exact field blocks so each pastes verbatim into the matching form field):
1. Asset: the in-scope asset (e.g. `https://github.com/example-org/example-framework`).
2. Weakness: the weakness name + CWE (e.g. "Server-Side Request Forgery (SSRF), CWE-918"); the researcher picks the
   matching HackerOne weakness dropdown.
3. Severity: the CVSS vector + score. Many programs now use CVSS 4.0 (axes
   AV/AC/AT/PR/UI/VC/VI/VA/SC/SI/SA); confirm the version per program from the current public policy, and do
   NOT default to 3.1. The form's calculator gives the authoritative score.
4. Title: one line (the vulnerability + the affected component/asset).
5. Affected version(s): the grounded range.
6. Affected file: a commit-PINNED GitHub blob permalink with a line anchor, so the triager lands on the exact
   lines (e.g. `.../blob/<full-sha>/path/file.ts#L11-L16`).
7. Description: the full markdown body (see Canonical section order below).
8. Impact: its own field (concrete, bounded).
9. Attachment: the PoC zip (often REQUIRED for a bounty).
Optional: Hacker summary (shown on public disclosure).

## Canonical section order

Web-app finding: Summary -> Steps to reproduce -> Expected vs actual -> Impact.
Framework / library finding (add): Summary -> Testing environment -> Steps to reproduce (numbered,
atomic, verbatim output) -> Expected vs actual -> Root cause (file:line + snippet + 1-2 sentences) ->
Suggested fix -> Affected versions -> References. Impact goes in its own platform field.

## Formatting

- Every command, request, response, code snippet, and tool output goes in a FENCED code block with a
  language hint (```js, ```bash, ```http, ```text). Never rely on 4-space indentation: on paste it is
  stripped and the text reflows as prose.
- Numbered lists for reproduction steps. Inline code for identifiers, paths, parameters.
- `##` headers per section. Bold rare (one field label or key finding per section).
- Tables ONLY for version ranges (affected / patched). A classification / impact "matrix" table reads
  as AI-generated; present that data as a verbatim fenced capture instead.
- No ASCII diagrams. Prefer real terminal captures and screenshots. Reference attachments as "attached",
  never "as shown above".

## Platform markdown gotchas

- HackerOne renders `==x==` as highlight, `~~x~~` as strikethrough, `**x**` as bold. Source code with
  `===` / `!==` / `==` MUST be inside a fenced block or it mangles (`===` renders as `=`, highlighted).
  Always fence code; after paste, check the review screen renders `===`/`!==` intact.
- The description field accepts markdown. Confirm tables and fences render on the review screen before
  submitting.

## Voice: strip every instance

- Hedges: could / might / appears / potentially / seems to.
- Self-justifying severity: critical, severe, extremely, "this is a serious issue", "not inflated",
  "honestly".
- Defining the bug class ("SSRF is a vulnerability where..."). The triager knows.
- Meta-commentary: "this report demonstrates", "in conclusion", "please do not dedup", "worth noting".
- Passive voice: "it was found that" -> "sending X returns Y".
- Caption narration: "as can be seen in the screenshot above".
- Preamble / pleasantries: "thank you for running this program".

Write active, declarative, factual. Let the CVSS vector and the captured output carry the weight.
No em/en dashes. No emojis.

## Per-field copy-paste hand-off

Hand off as a numbered, per-field walkthrough: emit each of the nine fields (1 Asset ... 9 Attachment) in its
own fenced code box, in order. Wrap the Description and Impact fields in FOUR-BACKTICK fences so their internal
triple-backtick code blocks survive the paste (the researcher selects all inside the box and pastes as-is). Give the
attachment as a file path in a box. The researcher pastes each field, checks the HackerOne review/render screen,
attaches the zip, and submits. The assistant never submits.

## Severity

- Give the full CVSS vector string, not just the number, and justify it per-metric in one tight line.
- State preconditions as facts in the Summary, not as apology. A bounded, accurate impact earns more
  triager trust than a stretched one.
- The program sets final severity. Do not lead with a severity adjective anywhere.

## Before / after

- Amateur: "This vulnerability is extremely critical and could potentially allow attackers to perform
  SSRF, which may lead to unauthorized access."
  Golden: "`/image` issues server-side requests to attacker-controlled URLs with no
  authentication. An attacker reaches an internal service the guard should block and reads its response."
- Amateur: "Navigate to the endpoint and try a malicious URL; you should observe an outbound request."
  Golden: "1. Send `GET /image?url=http://[internal]/x`. 2. The listener receives an inbound GET
  from the application server."
