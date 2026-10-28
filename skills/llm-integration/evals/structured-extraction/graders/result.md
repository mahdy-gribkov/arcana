---
type: llm
---
PASS: Uses tool calling or a JSON schema (structured outputs) rather than asking for JSON in the prompt and regex-matching it.
PASS: Validates the result with a schema library (for example Zod) and handles validation failure with a retry or an error.
FAIL: Parses the reply with a regex or JSON.parse on free text with no validation.
