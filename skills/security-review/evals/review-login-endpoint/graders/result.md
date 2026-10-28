---
type: llm
---
PASS: Flags the SQL injection and asks for a parameterized query.
PASS: Flags MD5 for passwords and asks for argon2 or bcrypt, with the hash compared in code, not in the query.
PASS: Flags the hardcoded JWT secret and the missing expiry, and asks for a secret from the environment or an asymmetric key.
PASS: Asks for rate limiting or lockout on the login route.
FAIL: Approves the endpoint or only comments on style.
