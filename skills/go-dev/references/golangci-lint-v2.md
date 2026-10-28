# golangci-lint v2: config, install, CI, troubleshooting

Sources: the golangci-lint.run migration guide and local install page; the reference release at the time of writing is v2.15.0
(api.github.com/repos/golangci/golangci-lint/releases/latest). Re-check the release page before pinning.

## Contents
- The v2 file shape
- Choosing linters
- Exclusions (tests, generated code, paths)
- Formatters
- Install and pinning
- CI
- Troubleshooting
- Migrating a v1 file

## The v2 file shape

The bundled starting point is `../assets/golangci.yml`. Its skeleton:

```yaml
version: "2"
run:
  timeout: 5m
linters:
  default: standard        # errcheck, govet, ineffassign, staticcheck, unused
  enable: [revive, bodyclose, gosec, errorlint, noctx, nolintlint, misspell, unconvert, unparam]
  settings: {}             # per-linter settings live HERE (v1: linters-settings)
  exclusions:
    generated: lax
    rules:
      - path: _test\.go
        linters: [gosec, noctx]
formatters:
  enable: [gofumpt, goimports]
  settings:
    goimports:
      local-prefixes: [example.com/yourmodule]
```

Every key below is a v1 key that no longer exists, so a config that uses one was written for v1:

| v1 | v2 |
| --- | --- |
| `enable-all: true` / `disable-all: true` | `linters.default: all` / `linters.default: none` (`standard` is the default set) |
| `linters-settings` | `linters.settings` |
| `gofmt`, `gofumpt`, `goimports`, `gci` as linters | the `formatters` section, settings in `formatters.settings` |
| `gosimple`, `stylecheck` | merged into `staticcheck` |
| `linters.presets` | gone; list the linters in `linters.enable` |
| `issues.exclude-rules` | `linters.exclusions.rules` |
| `issues.exclude-dirs`, `issues.exclude-files`, `run.skip-dirs`, `run.skip-files` | `linters.exclusions.paths` and `formatters.exclusions.paths` |
| `issues.exclude-use-default` | `linters.exclusions.presets` |
| `output.format`, `output.sort-results` | `output.formats` (keys such as `text`, `json`); results are always sorted |
| `severity.default-severity` | `severity.default` |

`run.timeout` is off by default in v2; keep an explicit value in CI so a hung analysis fails loudly.

## Choosing linters

- Start from `default: standard` and add by need. `default: all` makes every upgrade a surprise (new linters appear), so it needs a pinned
  version and a reviewed disable list.
- A linter earns its place by catching a bug class your project has hit: `bodyclose` (HTTP bodies), `errorlint` (`%w`, `errors.Is/As`), `noctx`
  (requests without a context), `sqlclosecheck`, `gosec`, `nolintlint` (every `//nolint` names a linter and a reason).
- `exhaustruct` has been deprecated since v2.13.0 (golangci-lint.run linters page): do not add it.
- List what a given version really has: `golangci-lint help linters`. Do not copy a linter list from an old blog post.

## Exclusions

- Tests: exclude `gosec` and `noctx` for `_test\.go` (`httptest.NewRequest` trips `noctx`). Never exclude them outside tests.
- Generated code: `exclusions.generated: lax` skips files carrying the standard "Code generated ... DO NOT EDIT" header.
- A `//nolint:linter // reason` on one line beats a path exclusion for a single false positive. `nolintlint` enforces the reason.

## Formatters

`golangci-lint fmt` formats, and `golangci-lint fmt --diff` prints what it would change (a clean tree prints nothing). `gofumpt` is the
stricter superset of gofmt; `goimports` needs `local-prefixes` set to the module path so imports group correctly.

## Install and pinning

- The official page says `go install`/`go get`, the "tools pattern" and `tool` directives "aren't guaranteed to work" and recommends the
  binary install. Download the `install.sh` script documented at golangci-lint.run/docs/welcome/install/local/, read it, then run it with
  a pinned version (for example v2.15.0). On Windows: `choco install golangci-lint` (the Scoop package is not maintained by the
  golangci team).
- Pin one version in CI and use the same one locally. A mismatch is the first suspect when the same code lints differently
  (`../scripts/go-check.mjs` compares the local binary with the pin it finds in `.github/workflows`). Fix the local tool; do not relax the config.

## CI

Use the official `golangci/golangci-lint-action` at a major version that supports v2 (v7 or later; confirm in the action README) with
`version:` set to the pin, after `actions/setup-go`. Add the vulnerability gate as its own step: `govulncheck ./...` (dependencies and
standard library, call-graph aware) and `go test -race ./...`. For a legacy codebase, report only new findings first
(`--new-from-rev=origin/main`), then burn the backlog down on a schedule; never switch a linter off to get green.

## Troubleshooting

| Symptom | First checks |
| --- | --- |
| `undefined: ...` or could not import in CI only | `go mod download`, a clean module cache (`golangci-lint cache clean`), build tags the CI job lacks, a `go.mod` `go` directive newer than the CI toolchain |
| Slow in CI | cache the Go build and module caches; run changed code only with `--new-from-rev`; raise `run.timeout` last |
| Local and CI differ | versions (see above), then the config path (`golangci-lint config path` prints the file in use), then build tags |
| A false positive | one `//nolint:name // reason` line; if the whole class is noise in tests, an exclusion rule scoped to `_test\.go` |
| Config rejected after an upgrade | `golangci-lint config verify` (validates against the schema); a v1 file needs `golangci-lint migrate` |

## Migrating a v1 file

`golangci-lint migrate` converts the file and backs the original up as `<name>.bck.<ext>`. It drops comments, deprecated options and unknown
fields, so diff the result by hand and re-add the explanations. Then run `golangci-lint run` and `golangci-lint fmt --diff` once and fix
what the new defaults report; do not widen the exclusions to hide it.
