# Go idioms: errors, HTTP, concurrency, modern stdlib

The baseline conventions are in `../SKILL.md` (handle every error, wrap with `%w`, context first, one structured logger, `errors.Is/As`).
This file holds the code shapes. Only the two newest Go releases are supported (go.dev/doc/devel/release); check go.dev/doc/go1.N before
using a feature newer than the module's `go` directive.

## Contents
- Three error shapes
- HTTP clients and servers
- Concurrency
- Logging
- Modern stdlib worth using
- Performance
- Anti-patterns

## Three error shapes

Sentinel for an expected condition, translated at the boundary and wrapped with both causes (Go 1.20+):

```go
var ErrNotFound = errors.New("not found")

func (s *Store) GetUser(ctx context.Context, id int) (*User, error) {
	user, err := s.db.Find(ctx, id)
	if errors.Is(err, sql.ErrNoRows) {
		return nil, fmt.Errorf("get user %d: %w", id, ErrNotFound)
	}
	if err != nil {
		return nil, fmt.Errorf("get user %d: %w", id, err)
	}
	return user, nil
}
```

Typed error when the caller needs data, extracted with `errors.As`:

```go
type ValidationError struct {
	Field   string
	Message string
}

func (e *ValidationError) Error() string { return fmt.Sprintf("invalid %s: %s", e.Field, e.Message) }

var validation *ValidationError
if errors.As(err, &validation) {
	logger.Warn().Str("field", validation.Field).Msg(validation.Message)
}
```

`panic` is for programmer errors that cannot be recovered (an impossible switch arm), never for input, I/O or a missing config.
`errors.Join` combines independent failures (closing several resources) into one error that `errors.Is` still sees through.

## HTTP clients and servers

Client: build the request with a context, use a client with a timeout (the default client has none), close the body, check the status.

```go
func fetchUser(ctx context.Context, client *http.Client, base, id string) (*User, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, base+"/users/"+url.PathEscape(id), nil)
	if err != nil {
		return nil, fmt.Errorf("build user request: %w", err)
	}
	resp, err := client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("fetch user %s: %w", id, err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("fetch user %s: unexpected status %d", id, resp.StatusCode)
	}
	var user User
	if err := json.NewDecoder(resp.Body).Decode(&user); err != nil {
		return nil, fmt.Errorf("decode user %s: %w", id, err)
	}
	return &user, nil
}
```

Server: the standard library mux has method and path-parameter patterns since Go 1.22, so a framework is optional.

```go
mux := http.NewServeMux()
mux.HandleFunc("GET /users/{id}", getUser)   // r.PathValue("id")
mux.HandleFunc("POST /users", createUser)
mux.HandleFunc("GET /files/{path...}", serveFile)
mux.HandleFunc("GET /health/{$}", healthCheck) // exact match

srv := &http.Server{
	Addr:              ":8080",
	Handler:           logging(mux),
	ReadHeaderTimeout: 5 * time.Second,
	ReadTimeout:       10 * time.Second,
	WriteTimeout:      30 * time.Second,
	IdleTimeout:       120 * time.Second,
}
```

Name the timeouts as constants when more than one server uses them. A server without `ReadHeaderTimeout` is a slow-client risk (gosec G112).

## Concurrency

`errgroup` for parallel work with error propagation and a concurrency cap (`SetLimit` replaces a hand-built semaphore). Since Go 1.22
each loop iteration has its own variable, so capturing `url` in the closure is correct on a module with `go 1.22` or newer:

```go
group, ctx := errgroup.WithContext(ctx)
group.SetLimit(10)
for _, url := range urls {
	group.Go(func() error { return fetch(ctx, url) })
}
if err := group.Wait(); err != nil {
	return fmt.Errorf("fetch all: %w", err)
}
```

Graceful shutdown: serve in a goroutine that reports its error, stop on the signal context, then give in-flight requests a deadline.

```go
ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt)
defer stop()

serveErr := make(chan error, 1)
go func() { serveErr <- srv.ListenAndServe() }()

select {
case err := <-serveErr:
	if !errors.Is(err, http.ErrServerClosed) {
		return fmt.Errorf("serve: %w", err)
	}
case <-ctx.Done():
	shutdownCtx, cancel := context.WithTimeout(context.Background(), shutdownTimeout)
	defer cancel()
	if err := srv.Shutdown(shutdownCtx); err != nil {
		return fmt.Errorf("shutdown: %w", err)
	}
}
return nil
```

Every goroutine has a parent that waits for it and a way to stop it (context cancellation). Channels are for handing a value to another goroutine;
a mutex is for protecting state. Run tests with `-race` (it needs cgo; see `../scripts/go-check.mjs`).

## Logging

Use one structured logger per module. `log/slog` (standard library since Go 1.21) is the default choice for a new module; in a module
that already uses zerolog or zap, stay with it rather than mixing two loggers. Never `fmt.Println` or `log.Println` outside `main`'s usage text. Never log tokens,
passwords or personal data; redact first.

## Modern stdlib worth using

- `slices` and `maps` (1.21): `slices.Sort`, `slices.Contains`, `slices.BinarySearch`, `maps.Clone`, `maps.DeleteFunc`.
- `for i := range n` and per-iteration loop variables (1.22); range-over-func iterators with `iter.Seq` (1.23).
- `testing.T.Context` and `testing.B.Loop` (1.24); `testing/synctest` for deterministic time and goroutine tests (1.25).
- `encoding/json` `omitzero` struct tag (1.24).

```go
func Lines(r io.Reader) iter.Seq[string] {
	return func(yield func(string) bool) {
		scanner := bufio.NewScanner(r)
		for scanner.Scan() {
			if !yield(scanner.Text()) {
				return
			}
		}
	}
}
```

An iterator that can fail should yield `(value, error)` pairs (`iter.Seq2[T, error]`), because `bufio.Scanner.Err()` is otherwise lost.

## Performance

Profile before optimizing. `go test -bench=. -benchmem -count=5 -cpuprofile=cpu.prof` then `go tool pprof -http=:8081 cpu.prof`. For a
running server import `net/http/pprof` on a localhost-only port, never on the public mux. Common wins after measuring: pre-size slices
(`make([]T, 0, n)`), `strings.Builder` in loops, `sync.Pool` for hot short-lived buffers, a context deadline on every external call.

## Anti-patterns

| Instead of | Write |
| --- | --- |
| `result, _ := doSomething()` | handle the error, or return it wrapped |
| `go func() { doWork() }()` | `group.Go(...)` or a goroutine with a parent that waits and a stop signal |
| `log.Println("something happened")` | one structured event with fields |
| `http.Get(url)` | a request with a context sent by a client with a timeout |
| `if err.Error() == "not found"` | `errors.Is(err, ErrNotFound)` |
| `time.Sleep` in a test to wait for a goroutine | a channel, a `WaitGroup`, or `testing/synctest` |
