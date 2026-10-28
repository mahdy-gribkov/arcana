# TypeScript idioms: errors, boundaries, signatures, async

The baseline conventions are in `../SKILL.md`. This file holds the code shapes. Banned-construct replacements (`any`, `!`, `as`), unions,
brands and generics are in `typescript-strict.md`.

## Contents
- Expected failures are values
- Unexpected failures throw with a cause
- Parse at the boundary
- Required values, no defaults
- Signatures: derive, do not pass twice
- Async

## Expected failures are values

A failure the caller can act on (invalid, not found, denied) is a value with a stable code. The caller branches on the code.

```ts
type RenameOutcome = 'ok' | 'NOT_FOUND' | 'NAME_TAKEN';

export async function renameProject(db: Database, projectId: string, name: string): Promise<RenameOutcome> {
    const existing = await findProject(db, projectId);
    if (existing === undefined) return 'NOT_FOUND';
    if (await nameInUse(db, name)) return 'NAME_TAKEN';
    await saveName(db, projectId, name);
    return 'ok';
}
```

Never branch on message text (`err.message.includes('UNIQUE')`). Translate the vendor error once, where it enters, into a code.

## Unexpected failures throw with a cause

```ts
try {
    return await mailer.send(message);
} catch (error) {
    throw new Error(`Failed to send the "${message.kind}" email through the provider: request rejected. Check the provider status and the API key.`, { cause: error });
}
```

- The message says what failed, why and what to try. The `cause` keeps the original for the log. Never put a token or personal data in the message.
- No empty `catch`. No `catch` that returns a value that looks valid:

```ts
// BAD: a database failure looks like "nothing changed", and the caller skips the correction
async function countChanges(db: Database): Promise<number> {
    try { return await queryChangeCount(db); } catch { return 0; }
}

// GOOD: the error path differs from a genuine zero, and the caller fails closed
async function countChanges(db: Database): Promise<number | undefined> {
    try { return await queryChangeCount(db); } catch (error) { logger.error({ err: error }, 'change count failed'); return undefined; }
}
```

- A dependency that is down fails closed (deny, retry later). Data that does not decode (a stale cache, a session blob) is treated as absent:
  delete it and re-derive, so one bad row cannot lock a user out for the key's whole lifetime.

## Parse at the boundary

Untrusted input (a request body, `JSON.parse`, a query string, a cookie, a database row with a JSON column) is parsed once into a typed
value. Downstream code trusts the type and does not re-check it.

```ts
const bodySchema = z.object({ email: z.string().email(), locale: z.enum(['en', 'he']) });

const parsed = bodySchema.safeParse(await request.json());
if (!parsed.success) return Response.json({ code: 'INVALID_BODY' }, { status: 400 });
const { email, locale } = parsed.data;
```

## Required values, no defaults

A value that a caller or an environment can forget has no default. Required means required in the type, and a missing value fails at the boundary.

```ts
// BAD: a forgotten timeout silently becomes 30 seconds, and a missing locale silently becomes English
function fetchReport(url: string, timeoutMs = 30_000, locale = 'en') { /* ... */ }

// GOOD: the call site must choose, and tsc says so when it forgets
interface FetchReportOptions { url: string; timeoutMs: number; locale: Locale }
function fetchReport(options: FetchReportOptions) { /* ... */ }
```

For environment and config, validate once at startup and throw a startup error naming the missing key. Do not write `env.X ?? 'fallback'`
and do not use zod `.default()` for such a value. When absence is a valid answer, put it in the type: `locale: Locale | undefined`.
A purely presentational default on a UI component prop (a size or a variant) is outside this rule; a default for behavior, limits or data
is not.

## Signatures: derive, do not pass twice

```ts
// BAD: two parameters that must agree, then a runtime check that they do
send(kind: MailKind, sendClass: SendClass, to: string, subject: string, html: string, locale: Locale, tenant: string, replyTo?: string, tag?: string)

// GOOD: one options object; the class follows from the kind in one table
const SEND_CLASS = { welcome: 'transactional', newsletter: 'advertisement' } as const satisfies Record<MailKind, SendClass>;
send({ kind, to, subject, html, locale, tenant })
```

More than three parameters, or a boolean parameter, becomes an options object or two functions (`sendNow` and `sendLater`, not `send(true)`).
Derive types from their source (`typeof ROUTES`, `z.infer<typeof schema>`, an ORM's inferred row type) instead of writing them twice.

## Async

- `async`/`await`; independent reads run together with `Promise.all`. Work that must outlive the response goes through the runtime's
  after-response hook (`after()` in Next.js, `waitUntil` on edge runtimes), not a floating promise.
- A timeout is `AbortSignal.timeout(ms)` with a named constant. Never an arbitrary delay to fix ordering.
- Every promise is awaited, returned or handed to that hook. A floating promise is a lost error.
