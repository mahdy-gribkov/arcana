# Pooled clients and shared state

Read this when the code touches Redis, HTTP, SQL or any pooled client, or when several workers can see the same message or key.

## Clients and resources

- One client per process, not per request. A go-redis `Client` (like `*sql.DB` and `*http.Client`) is a pool that is safe for concurrent
  use: construct it once at startup and reuse it. Source: go-redis issue 166 (github.com/redis/go-redis/issues/166) and the redis.io Go
  client guide.
- Context is the first parameter and never a struct field. Every network call on a request path carries a deadline. A startup ping may use
  `context.Background()` when the client's own dial and read timeouts already bound it, so do not add a bespoke `context.WithTimeout` or a
  timeout knob for it. Source: Google Go style decisions (google.github.io/styleguide/go/decisions).
- Validate eagerly on construct: a constructor pings, opens or dials and returns the failure instead of deferring it to first use.
  Distinguish the failure kinds a caller will act on (see the typed-error rule in `review-checklist.md`).
- Handle the driver's sentinel idiomatically. For go-redis a miss is `redis.Nil`; treat it as a miss and everything else as an error, and
  never let a miss fall through an `err != nil` log path. Translate it to the package's own `ErrNotFound` at the boundary.
- Document lifetime semantics where they bite. For a TTL: relative to now, does it replace an existing TTL, what if the key is absent.
  One sentence on the method saves the reader a trip to the driver docs.
- Close what you open: `rows.Close()` (sqlclosecheck), `resp.Body.Close()` (bodyclose), and `defer` immediately after the error check.

## Distributed and shared-state safety

- Never unconditionally `DEL` a key that can expire and be reclaimed. If a claim or lock key can lapse by TTL and another worker takes
  it, a blind `DEL` on the way out deletes the new holder's key. Either compare-and-delete against a token that proves you still hold it, or do not
  release at all and let it expire. Prefer the leaner option; reach for a Lua compare-and-delete only when releasing early matters.
- At-least-once delivery means idempotent or single-emit. A consumer that can see the same message twice (a queue, a webhook, a retried
  job) must either be idempotent under a stable dedup key (a unique index, a seen-set) or claim once and not retry. Decide which before
  writing the handler.
- Shared-infrastructure config is defined by the existing consumer, not by your file. Before adding a client to a shared store, read how
  the current consumer connects: a managed store with an ACL username and TLS means you set the username and enable TLS too. Shape
  emitted events to what the consumer already reads. Read the consumer's contract before writing the producer.
- Fail closed when the dependency is down; self-heal when the data is poisoned. A cached or session record that fails to decode or
  validate is treated as absent (delete it, re-derive or re-prompt), never as a lockout that persists for the key's whole TTL.
  Connectivity failure fails closed; a corrupt value is dropped and rebuilt.
