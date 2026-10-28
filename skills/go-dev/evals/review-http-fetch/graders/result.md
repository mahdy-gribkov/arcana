---
type: llm
---
PASS: Flags the unclosed response body (bodyclose), the ignored Decode error, and the missing status code check.
PASS: Asks for a context.Context first parameter with http.NewRequestWithContext and a client with a timeout, instead of the default client.
PASS: Asks for the id to be path-escaped and for the returned errors to be wrapped with fmt.Errorf and %w.
FAIL: Approves the function or only comments on naming and formatting.
