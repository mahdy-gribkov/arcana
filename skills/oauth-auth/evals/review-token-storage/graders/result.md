---
type: llm
---
PASS: Flags the missing PKCE code challenge and verifier, and asks for the S256 method.
PASS: Flags Math.random() for state, asks for a cryptographically random value, and asks for the state to be validated on the callback.
PASS: Flags tokens in localStorage as readable by any XSS and recommends httpOnly, Secure, SameSite cookies.
FAIL: Approves the flow or only comments on code style.
