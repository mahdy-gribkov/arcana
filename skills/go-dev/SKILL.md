---
name: go-dev
description: Writes, reviews and lints Go code, with idiomatic error handling, table-driven tests, golangci-lint v2 configuration, and a one-command run of format, lint, vet, tidy, govulncheck and race tests. Use when working on a .go file or go.mod, reviewing a Go PR or function, asking "is this idiomatic Go", setting up or fixing golangci-lint, writing Go tests, or chasing a Go lint, vet or race failure. Not for other languages.
allowed-tools: Read, Glob, Grep, Bash(node ${CLAUDE_SKILL_DIR}/scripts/go-check.mjs:*)
---

# Go development and review

Scope: anything in `.go` files or `go.mod`. This skill adds the how-to and the review method on top of a short baseline of Go
conventions. If the project already has its own written Go conventions, they win over the baseline below.

## Baseline conventions

- Handle every error; never discard one with `_` unless a comment says why that is safe.
- Wrap with `%w` and add context (`fmt.Errorf("get user %d: %w", id, err)`); compare with `errors.Is` / `errors.As`, never by message.
- `context.Context` is the first parameter of anything that does I/O, and is never stored in a struct.
- One structured logger per module (`log/slog`, zerolog or zap, whichever the module already uses). No `fmt.Println` for logging.
- Table-driven tests for every new function, with named cases.
- No secrets or personal data in logs or error messages.

## Workflow

1. **Know the module.** Read `go.mod` (module path, `go` directive), the lint config (`.golangci.yml`) and `.github/workflows` for the
   pinned golangci-lint version. A repo with no lint config is the first finding.
2. **Run the mechanical gates before judging anything.**
   `node ${CLAUDE_SKILL_DIR}/scripts/go-check.mjs <module-dir>` (add `--fast` to skip govulncheck and the test run). It prints one
   PASS, FAIL, MISS or WARN line per gate: format, `golangci-lint run`, `go vet`, `go mod tidy -diff`, `govulncheck`, `go test -race`.
   It uses the repo's own lint config, else the baseline in `assets/golangci.yml`, and says which. A MISS line means a tool is not
   installed: report it and install the pinned version; do not skip the gate. Exit 2 means the directory has no `go.mod`.
3. **Review the judgment items** in `references/review-checklist.md`. Never restate lint output; the tool line is the finding.
4. **Write the findings** in the format of `references/review-output.md` (file:line, why, fix with an effort estimate, source).
5. **Writing new code or tests?** Pick the reference from the table, write it, then run the gates again.

## Which reference

| Task | Read |
| --- | --- |
| Error shapes, HTTP client or server, concurrency, shutdown, logging, modern stdlib, performance | `references/idioms.md` |
| Writing or fixing Go tests, fakes, fuzz, benchmarks, the `-race` run | `references/testing-go.md` |
| Review judgment: naming, interfaces, errors, modules, comments, commits | `references/review-checklist.md` |
| Writing up review findings | `references/review-output.md` |
| Creating, migrating or debugging `.golangci.yml`; install; CI pin; version drift | `references/golangci-lint-v2.md` |
| Redis, HTTP, SQL or other pooled clients; locks, dedup, at-least-once delivery | `references/shared-state-and-clients.md` |

Related skills: `testing` covers TypeScript and JavaScript tests, `ci-cd-pipelines` covers wiring the gates into CI, `security-review`
covers a deeper security pass than gosec and govulncheck give.

## Rules that bite

- golangci-lint is v2. A config with `enable-all`, `disable-all`, `linters-settings`, `skip-dirs`, `issues.exclude-rules`, `gosimple`
  or `typecheck` is a v1 file: run `golangci-lint migrate`, then diff it. Install the pinned binary (the official page discourages
  `go install`); pin the same version locally and in CI.
- Fix the code, never the gate: no `//nolint` without a linter name and a reason, no exclusions outside `_test.go` for `gosec` or `noctx`,
  no lowered thresholds.
- `go-check` is only as good as the installed tools. Say which gates did not run (MISS, skipped race) in the review, so "green" is not
  claimed on a partial run.
- Verify a version-gated language or library feature against the release notes (go.dev/doc/go1.N) and the module's `go` directive before
  using or recommending it.
- A problem found outside the change under review is still a finding: put it in the plan or an issue that names the layer which fixes it.

## Evidence

Cite file:line for every claim about the code. Quote the failing `go-check` line for every claim that a gate fails. Do not call a change
safe to merge without a green `go-check` (or a stated list of the gates that could not run).
