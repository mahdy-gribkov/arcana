---
type: llm
---
PASS: Uses the SDK streaming API and forwards text deltas to the client (server-sent events or a streamed response).
PASS: Reads the API key from an environment variable with a clear startup error when it is missing, never hardcoded.
PASS: Handles errors and client disconnect (abort the upstream stream) and sets max_tokens.
FAIL: Waits for the full response before sending anything.
