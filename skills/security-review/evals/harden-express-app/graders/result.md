---
type: llm
---
PASS: Lists security headers including Strict-Transport-Security, X-Content-Type-Options and Content-Security-Policy.
PASS: Uses an explicit CORS origin allowlist, not a wildcard together with credentials.
PASS: Covers CSRF for cookie sessions with SameSite cookies or a CSRF token.
PASS: Sets httpOnly, Secure and SameSite on the session cookie, and adds rate limits with a stricter limit on auth routes.
FAIL: Gives only a generic list of advice with no concrete configuration.
