# Go review checklist (judgment only)

Run `../scripts/go-check.mjs` first. Everything a linter reports is settled by the tool; this list covers what a tool cannot decide. Each
rule carries its reason and a source, so it teaches instead of dictating. Verify a version-gated claim against the Go release notes
(go.dev/doc/go1.N) before repeating it. The baseline conventions in `../SKILL.md` (error wrapping, context first, one logger, table
tests, `errors.Is/As`) are not repeated here.

## Contents
- Naming
- Interfaces and abstraction
- Errors
- Modules
- Control flow, comments, constructors, concurrency
- Commits and PRs

## Naming

A name is read by a person first, so it must be honest (says what the thing is or does) and legible to someone who does not know the
code. The linter gates the mechanical part (case, stutter, exported doc); honesty and readability are judgment.

- Name a thing for what it does, with no invented or abstract label. `ParticipantRoster` for a type that lists a meeting's participants
  implies a concept that is not there; `ParticipantLister` with a `participants` field matches the `-er` precedent. Survey sibling
  types with Grep and match the real convention.
- Name a type or package for the job, not the driver. `redisclient.Client` names the driver twice and the job zero times; a KV store is
  `kv` / `KV`.
- Readability over terseness: a bare single letter is not a name. Exceptions are a loop index and a method receiver. Short receivers
  are standard Go, so raise a long one once as a preference and never block a change over it.
- Avoid stutter (`foo.Thing`, not `foo.FooThing`). No `Get` prefix on a getter. Package names are short, lowercase, with no
  underscores or mixedCaps. Sources: Effective Go; Google Go style decisions (google.github.io/styleguide/go/decisions).

## Interfaces and abstraction

- An interface has to earn its place. One implementation does not justify it. It earns it by buying something concrete, most often an
  in-memory fake so consumers can test without the real backend. Name the payoff in the review; "abstraction is good" is not a reason.
- When a reviewer names a lean fix, lean beats clever: implement that, not a more elaborate version you then have to unwind.
- If an interface exists for a fake, add one shared behavior test that the real backend and the fake both run, so they cannot drift
  (a fake returning a less detailed error than production is a real bug no per-implementation test catches). This is a recommended
  practice; the public style guides do not prescribe it.
- Accept interfaces, return concrete structs. Sources: Google Go style decisions; Effective Go.
- Assert compliance at compile time: `var _ KV = (*Client)(nil)`, so drift is a build error. Source: Uber Go style guide.
- Prefer dependency injection to a mutable package-level global. Sources: Uber Go style guide; Google best practices. A process-wide
  singleton that is genuinely one pool (a connection pool) is a deliberate exception; the direction that satisfies both is an injected
  handle. Do not refactor it inside an unrelated change.

## Errors

- Wrap with `%w`, more than once when there is more than one cause. `fmt.Errorf("%w: %v", ErrX, err)` flattens the driver's error to
  text; since Go 1.20, `fmt.Errorf("%w: %w", ErrX, err)` keeps both in the chain for `errors.Is` / `errors.As` (go.dev/doc/go1.20).
- Wrapping is an API commitment: `%w` makes the wrapped error part of the contract. Use `%v` when the cause is deliberately hidden
  (go.dev/blog/go1.13-errors).
- Domain sentinels are named `ErrXxx` (staticcheck ST1012). Translate the driver's sentinel at the boundary so callers never import the
  driver to branch on a miss.
- Carry detail: a not-found error names the key that missed. `errors.Is` still matches and the log is useful.
- A typed error earns its place like an interface: add it when a caller will branch on it; trace the callers first.

## Modules

- No nested per-package `go.mod` for "dependency isolation". `go build` compiles only what you import and module graph pruning (Go 1.17+)
  already keeps unrelated requirements out (go.dev/ref/mod). A nested module costs coverage: `go test ./...` in the parent silently
  skips it, so it needs its own CI job if it must stay separate.
- `go mod tidy` hygiene: a direct import is never `// indirect`; the `go` directive matches the toolchain. The check script runs
  `go mod tidy -diff`.

## Control flow, comments, constructors, concurrency

- Handle the error first and reduce nesting; drop the `else` after a terminating branch. Sources: Effective Go; Uber Go style guide.
- Comments: default none. Keep only comments that preserve a decision the code cannot express: a public contract, a security boundary,
  a concurrency or lifecycle invariant, an external quirk, a deliberate deviation. Exported names get the one-line doc comment the
  linter requires, no more; a `//nolint` gets a few-word reason. Flag restatement and narration for removal, and flag a missing note on a
  security boundary the same way.
- Table-driven tests (see `testing-go.md`). Functional options for a constructor with many optional knobs. Sources: Uber Go
  style guide; Google best practices.
- No fire-and-forget goroutines. A background loop has a managed, cancelable lifetime (`errgroup`, a context, a `WaitGroup`). Source:
  Uber Go style guide.

## Commits and PRs

- One logical change per commit; the subject says what it does. Mark a breaking change with `!` (`refactor(kv)!: rename Client to KV`).
- `Example` functions live in an external test package (`package foo_test`): the one place that exercises the import path a consumer uses.
- When a package moves or renames, repoint its docs (install lines, imports, READMEs). A quickstart that dies at `go get` is worse than none.
- A commit that does not build on its own says so and why (keeping git's rename detection is legitimate).
