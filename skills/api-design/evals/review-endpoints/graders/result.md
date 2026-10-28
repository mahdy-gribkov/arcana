---
type: llm
---
PASS: Flags verbs in the paths and asks for plural noun resources with HTTP methods, for example GET /users/{id} and DELETE /orders/{id}.
PASS: Flags returning 200 for failures and asks for proper status codes such as 400, 404 and 422.
PASS: Asks for a consistent error body, ideally RFC 9457 problem details with application/problem+json.
PASS: Mentions versioning, for example a /v1 prefix.
FAIL: Approves the design or only suggests renaming one endpoint.
