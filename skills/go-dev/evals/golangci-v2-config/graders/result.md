---
type: llm
---
PASS: Writes a v2 config: version "2", linters.default standard plus an explicit enable list, and a formatters section (gofumpt, goimports) instead of listing them as linters.
PASS: Puts path exclusions under linters.exclusions and tells the user to pin the golangci-lint version in CI and locally (binary install or the official action).
FAIL: Uses v1 keys: enable-all, disable-all, linters-settings, run.skip-dirs, issues.exclude-rules, gosimple or typecheck.
