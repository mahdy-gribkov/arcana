# Testing Go

The baseline in `../SKILL.md` requires table-driven tests for every new function. This file shows the shapes and the traps. The `testing`
skill covers TypeScript and JavaScript; nothing here applies to vitest or Playwright.

## Contents
- The table test
- Helpers, parallel tests, cleanup
- HTTP handlers and clients
- Fakes that cannot drift
- Fuzzing and benchmarks
- Running the suite

## The table test

One table, named cases, one assertion path. Compare errors with `errors.Is` / `errors.As`, never by message.

```go
func TestParseSize(t *testing.T) {
	tests := []struct {
		name    string
		input   string
		want    int64
		wantErr error
	}{
		{name: "bytes", input: "100B", want: 100},
		{name: "kilobytes", input: "2KB", want: 2048},
		{name: "empty", input: "", wantErr: ErrEmptySize},
		{name: "unknown unit", input: "5XB", wantErr: ErrUnknownUnit},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := ParseSize(tt.input)
			if !errors.Is(err, tt.wantErr) {
				t.Fatalf("ParseSize(%q) error = %v, want %v", tt.input, err, tt.wantErr)
			}
			if got != tt.want {
				t.Errorf("ParseSize(%q) = %d, want %d", tt.input, got, tt.want)
			}
		})
	}
}
```

`errors.Is(err, nil)` is true only when `err` is nil, so the one comparison covers the success and the failure rows. A case name says the
scenario, not the number. Failure messages print the input, the got value and the want value, in that order.

## Helpers, parallel tests, cleanup

- A helper calls `t.Helper()` first so a failure points at the calling line.
- `t.Parallel()` only on tests that share no state; the loop variable is per-iteration since Go 1.22, so no copy is needed.
- Use `t.Cleanup`, `t.TempDir()` and `t.Setenv` instead of manual teardown. `t.Context()` (Go 1.24) is canceled when the test ends.
- A test never sleeps to wait for a goroutine. Use a channel, a `sync.WaitGroup`, or `testing/synctest` (Go 1.25) for time-driven code.
- Fixture files live in `testdata/` (the toolchain ignores that directory). Golden files are written by a `-update` flag and reviewed in
  the diff, never regenerated silently in CI.

## HTTP handlers and clients

Handlers: `httptest.NewRecorder` and `httptest.NewRequest`, then assert status, headers and body. Clients: `httptest.NewServer` with a
handler that returns the case's response, and point the client at `server.URL`; this exercises the real transport instead of a mock.
Always close the server with `t.Cleanup(server.Close)`.

## Fakes that cannot drift

Prefer a small in-memory fake over a generated mock, and run one shared behavior suite against both the fake and the real backend:

```go
func runKVBehavior(t *testing.T, newStore func(t *testing.T) KV) {
	t.Run("miss returns ErrKeyNotFound with the key", func(t *testing.T) {
		_, err := newStore(t).Get(t.Context(), "absent")
		if !errors.Is(err, ErrKeyNotFound) {
			t.Fatalf("Get(absent) error = %v, want ErrKeyNotFound", err)
		}
	})
}

func TestMemoryKV(t *testing.T) { runKVBehavior(t, func(*testing.T) KV { return NewMemoryKV() }) }
func TestRedisKV(t *testing.T)  { runKVBehavior(t, newRedisForTest) } // skipped when no server is configured
```

A test that needs an external service skips itself with a message that names the environment variable, instead of failing on a
laptop that lacks it.

## Fuzzing and benchmarks

```go
func FuzzParseSize(f *testing.F) {
	f.Add("100B")
	f.Fuzz(func(t *testing.T, input string) {
		if _, err := ParseSize(input); err != nil {
			return // an error is a valid answer; the property is "never panics"
		}
	})
}

func BenchmarkParseSize(b *testing.B) {
	for b.Loop() { // Go 1.24+; before that: for i := 0; i < b.N; i++
		if _, err := ParseSize("2KB"); err != nil {
			b.Fatal(err)
		}
	}
}
```

Fuzz targets state an invariant (no panic, round trip, idempotence). Benchmarks run with `-benchmem -count=5` and are compared with
`benchstat`; one run is not evidence.

## Running the suite

- `go test -race -count=1 ./...` is the CI shape. `-count=1` defeats the test cache. The race detector needs cgo, so on a machine
  without a C compiler run it in CI.
- `go test -run '^TestParseSize$/^kilobytes$'` runs one case.
- Coverage: `go test -coverprofile=cover.out ./...` then `go tool cover -func=cover.out`. Coverage finds untested code; it does not prove
  the tests assert anything.
- `../scripts/go-check.mjs` runs vet, lint, tidy, vulnerabilities and the race tests in one pass.
