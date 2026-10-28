---
type: llm
---
PASS: Stores only a hash of the refresh token, not the token itself.
PASS: Issues a new refresh token on every use and marks the old one as replaced or revoked.
PASS: Detects reuse of an already replaced token and revokes the whole token family.
PASS: Suggests a shorter refresh lifetime than 30 days or an absolute session limit.
FAIL: Keeps one long-lived refresh token and only adds an expiry check.
