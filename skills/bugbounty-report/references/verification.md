# Invalidation gauntlet

Run this BEFORE writing the report, and again before declaring done. It is not a confirmation checklist: it
is a set of ordered gates, each returning KEEP or KILL. Any KILL means the finding is not submittable as
claimed. A clean KILL, or a downgrade to conditional/informative, is a valid and valuable result, not a
failure. Record the verdict for every gate in the evidence ledger. The goal is to kill a weak finding here,
before a triager does it publicly and costs reputation. Every load-bearing claim maps to a file:line, a
command output, or a primary-source URL. Re-derive; do not assert from memory or from a prior session's label.

## The gates (ordered cheapest-first; stop at the first KILL)

- **G0 Freshness (re-verify the static homes).** Policies, program scope, and CVSS method are volatile (they
  change often). Before relying on any static home (this skill, a memory, a rule) for a
  volatile fact, re-verify that fact against CURRENT public sources, dated. Sourcing order: public web ->
  codebase -> local static homes -> the researcher as last resort. If current reality differs from the static
  home, use current reality AND update the home. Never submit on a stale policy.

- **G1 Novelty / duplicate.** Search the project's PUBLIC advisories, CVEs, and issue tracker for the same
  root cause. KILL if the same root cause is already reported or fixed. A related-but-different root cause is
  KEEP (note the distinction for the report).

- **G2 Lab / config artifact.** Does the bug reproduce on a realistic, default-ish setup, or only because of
  a non-default flag, an unusual config, or a lab shortcut you introduced? Strip each non-default piece and
  re-test. KILL if it only reproduces under a configuration a real deployment would not run.

- **G3 Framework vs application responsibility.** Who owns the fix? If the vulnerable behavior is the
  application misusing an API as documented, it is app-responsibility (informative), not a framework bug.
  Strongest KEEP signal: the framework itself tries to handle this case elsewhere (a guard, a throw, a
  documented isolation), so a gap on a parallel path is the framework failing its own contract. KILL / mark
  informative if the framework never claims to handle it and the docs put the responsibility on the app.

- **G4 Precondition realism (the hard gate).** Name every precondition the PoC needs. For each, is there a
  PLAUSIBLE REAL-WORLD instance, or did you construct the pattern because the vuln needs it? Pre-commit the
  bar BEFORE searching: decide what evidence (a public code-search hit, a documented pattern, a real app)
  would clear it, and what absence kills it. Then search. KILL / downgrade to conditional if no plausible
  real instance turns up. Decide the rule first; do not rationalize after seeing results.

- **G5 Reachability / attacker model.** Is it attacker-initiated, or a coincidence/race that needs unrelated
  actors to align? State exactly what must happen and who triggers it. A non-attacker-initiated race is not a
  KILL, but it caps severity (feed into G9).

- **G6 Runtime proof from clean.** No observable crash/leak/state-change on a runtime reproduction = not a
  finding. Reproduce from clean per the protocol below. KILL if it does not reproduce from the packaged files.

- **G7 Affected-version range, grounded.** Do not claim "X+" from a hunch. Confirm the version at runtime,
  and bound the range: find (git log/blame) when the vulnerable code was introduced, and confirm it is
  present through the current release. State from-version to current-version, each grounded.

- **G8 Not already patched.** Check the file's recent history AND the latest pre-release/canary, not just the
  stable you tested. KILL if a fix has landed in any current channel.

- **G9 Honest severity + triager deflation.** Assign the CVSS vector the evidence supports, then apply the
  deflation a skeptical program triager will: self-hosted-only, niche config, non-default, coincidence-gated,
  and app-precondition findings get marked down. State preconditions as facts, not apology. If the honest
  result is Low/informative, say so; a bounded accurate impact earns more trust than a stretched one.

## Calibration (anti-retrofit)

When you author or edit these gates, back-test them against findings you have already correctly killed or
parked, not only the one you want to pass. A gate set that does not cleanly kill an app-responsibility finding
or park a by-design/precondition-gated one has been shaped to pass your current finding. Fix the gates.

## Reproduce from clean (G6 detail)

- Tear down all prior state. Run ONLY the packaged PoC files, following the packaged README verbatim, as a
  reviewer would. A reproduction that needs steps you did by hand is not reproducible.
- Confirm the control (should-be-blocked) AND the exploit (should-succeed) both behave as claimed, with a
  positive control proving the harness is live.
- Guard against a false negative: if the result depends on environment/config, add a sanity check that aborts
  loudly with the fix, so a misconfigured run cannot look like "not vulnerable".
- The captured evidence (logs/JSON) matches the report's verbatim output (same nonce/timestamps).

## Package hygiene (scan every file in the zip)

Run the package scanner first (SKILL.md workflow step 3); it covers the personal data, secret, endpoint and dash bullets mechanically. Read what it cannot judge.

- No emails, usernames, local user paths (for example /home/<name> or a Windows profile folder), machine names.
- No secrets/tokens/keys.
- No client/employer/personal identifiers.
- No external/production endpoints in scripts (reserved test domains are fine).
- No em/en dashes, no emojis in source files and comments.
- Comments are factual and professional; code uses the project's standards; no dead code.
- Evidence response bodies are from your own infra (not proxied third-party data).

## Report render check

- Paste the report into the platform and read the REVIEW screen: fenced code renders monospace with operators
  intact (`===`/`!==` not mangled, no stray highlight), tables render, numbered steps hold.
- The local source-of-truth file matches the pasted fields verbatim.

## Evidence ledger (write it down)

One row per load-bearing claim: claim -> evidence (file:line / command output / URL) -> verdict, plus one row
per gate G1-G9 with its KEEP/KILL verdict. Do not exit to "write the report" with any gate unresolved or any
load-bearing claim unverified. Stale "done/verified/confirmed" labels from a prior session are claims to
re-check, not facts; a severity assigned before this gauntlet existed is provisional until the gates clear.

## Tooling notes

- Prefer a disposable container/VM for the reproduction so teardown is clean and nothing touches the host or
  any live system.
- Kill loops that match on process cmdline can match the killer shell itself; match on the executable path.
- Binary response bodies serialized into JSON as text are lossy; if faithful evidence matters, capture length
  + a hex/base64 prefix, but do not hand-edit captured evidence after the fact.
