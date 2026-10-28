# Pre-submit compliance

Platform structure is static (see the skill's HackerOne basics). PROGRAM facts and platform POLICIES are
VOLATILE (they change often) and, for a public program, are PUBLISHED PUBLICLY. Re-verify them from CURRENT
public sources every submission and date them (the program's public policy page, the vendor's bounty blog or
security page, public docs, reputable mirrors). Sourcing order: public web -> codebase -> local static notes
(which can be stale) -> the researcher as the LAST resort (only when a fact is not findable in public sources
or code). Never LOG IN to or scrape content behind an authenticated or private page; a JS-shell fetch is a
method failure (try another public source), not proof the data is private.

## Platform reference URLs (PUBLIC only; never fetch auth-gated program or gated docs pages)

- Finder Terms: https://www.hackerone.com/terms/finder-2023
- Code of Conduct: https://www.hackerone.com/policies/code-of-conduct
- Disclosure Guidelines: https://www.hackerone.com/terms/disclosure-guidelines
- Requesting Disclosure: https://docs.hackerone.com/en/articles/8475358-disclosure
- Privacy Policy: https://www.hackerone.com/privacy
- Clear Rules of Engagement: https://www.hackerone.com/policies/clear-rules-of-engagement
- Signal Requirements: https://docs.hackerone.com/en/articles/8505319-signal-requirements

## Program facts to re-verify from CURRENT public sources before writing (ask the researcher only as a last resort)

- Scope: is the exact asset or repo in scope, and which tier? Is this vulnerability class a named accepted category?
- Rules of engagement: production testing forbidden? local or own-infra PoC required? no automated
  scanning / no DoS?
- Required artifacts: repro steps, affected version, PoC zip (often REQUIRED for a bounty, not optional),
  affected-file permalink, patch suggestion. A program that lists a field as required auto-returns the
  report as "Needs More Info" when it is missing, so read the program's own required-fields list.
- Reporting channel: some projects run BOTH a HackerOne bounty and a security-email or GHSA channel. Pick
  one; do not cross-submit. A bounty wants the platform channel.
- Severity method (for example CVSS 4.0) and the minimum score for any reward (tier floor).
- Safe harbor conditions (usually: no production testing, follow policy, hold confidential).
- Signal and trial-report caps for new researchers.
- Program still open? Query HackerOne's public GraphQL (no auth): `curl -s -X POST https://hackerone.com/graphql
  -H "Content-Type: application/json" -d '{"query":"{ team(handle:\"HANDLE\"){ offers_bounties submission_state } }"}'`.
  `submission_state: "paused"` = closed to new reports. Quote the raw fields; never infer from an email.
- Live-testing rules: some programs allow live testing only on accounts or stores you created yourself, and
  forbid contacting their support. Record the exact rule and test within it.

## Pass/fail checklist

Content:
- [ ] No third-party PII anywhere in report or attachments.
- [ ] No production or third-party confidential data; no exfiltrated data beyond the minimum to prove impact.
- [ ] No hardcoded real credentials, tokens or keys.
- [ ] PoC is your own; any borrowed technique is attributed.
- [ ] PoC scripts contain no hardcoded external or production endpoints (reserved test domains like
      example.com per RFC 2606 are fine). Any "target" is local or own-infra.
- [ ] Response bodies in evidence originate from your OWN infrastructure, not a proxied third-party
      production response. If not, redact to status + minimal bytes.
- [ ] No PII, secrets, local user paths, usernames or emails in any packaged file (scan them).

Testing / RoE:
- [ ] All testing on self-owned or explicitly authorized infra. No production of the target.
- [ ] Stopped at minimum necessary to prove impact (no lateral movement, no metadata-then-pivot,
      no DB dump).
- [ ] No DoS and no automated scanning unless the program allows it in writing.

Disclosure / confidentiality:
- [ ] Hold the report confidential. Public disclosure is program-controlled; publishing before program
      approval is a Code-of-Conduct violation (ban risk).
- [ ] If the program is private, do not reveal its existence, scope or communications.
- [ ] Citing a third party's ALREADY-PUBLIC disclosure of a different or related bug inside the private
      report is allowed (public prior art, not disclosure).

Quality / eligibility:
- [ ] Claims verified, not speculative (fabricated claims violate the Code of Conduct).
- [ ] Reproducible from clean (see verification.md). PoC zip attached directly to the report, not
      third-party hosted.
- [ ] Not a duplicate: search the project's published advisories for the same root cause before filing.
- [ ] Severity is the accurate CVSS vector; expect the program to adjust (often down for niche or self-hosted).

## Common first-timer failures (auto-reject / penalty)

Public disclosure before approval; PII or real-user data in screenshots; over-exploitation past proof;
third-party-hosted evidence; unreproducible PoC; ignoring the program's own policy; cross-submitting to
two channels.
