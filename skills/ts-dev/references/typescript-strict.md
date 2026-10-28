# TypeScript strict: recommended baseline and the patterns that pass it

Generic examples often use `any`, `as any`, `raw as UserId` brand casts, object `type` aliases and `console.error`. All of them fail the
strict baseline below. The patterns here are the ones that pass it. Error values, boundary parsing and required config values are in
`idioms.md`.

## Contents
- The compiler and lint baseline
- Replacing the banned constructs
- Unions, exhaustiveness and result codes
- Branded and nominal types
- Generics, mapped, conditional and template types
- Async and errors (pointer)
- Constants and magic values
- Regex

## The compiler and lint baseline

A recommended starting point for a new project. An existing project keeps its own settings unless a finding is about to be filed
against them.

- `tsconfig`: `strict`, `noImplicitReturns`, `exactOptionalPropertyTypes`, `noUncheckedIndexedAccess`, `noImplicitOverride`,
  `noFallthroughCasesInSwitch`, `isolatedModules`, a current ES target, and `moduleResolution: bundler` for bundled apps. Framework apps
  (Next.js) keep the framework's own tsconfig and layer these flags on. Use the current stable TypeScript. `@total-typescript/ts-reset` is
  optional; it makes `JSON.parse` and `.json()` return `unknown`, not `any`.
- ESLint: typescript-eslint `strictTypeChecked` plus `stylisticTypeChecked` (the typed presets). Rules worth keeping as errors in
  non-test source: `no-explicit-any`, `no-non-null-assertion`, `ban-ts-comment`, `no-unsafe-type-assertion`,
  `no-unsafe-assignment/member-access/call/return/argument`, `no-unnecessary-condition`, `explicit-module-boundary-types`,
  `consistent-type-definitions: interface`, `prefer-nullish-coalescing`, `no-unnecessary-boolean-literal-compare`, `no-floating-promises`,
  `only-throw-error`, `eqeqeq`, `no-console`, and an unused-imports rule. Test files may relax `!` (`mock.calls[0]![0]`) and `console`.
- `exactOptionalPropertyTypes` means an optional property cannot be assigned `undefined`. Build the object conditionally
  (`...(value === undefined ? {} : { value })`) instead of passing `undefined`.
- `noUncheckedIndexedAccess` means `array[i]` and `record[key]` are `T | undefined`. Narrow with an early return, `at()`, or a guard; do not
  add `!`. A branch the types force but runtime cannot reach carries an honest `/* v8 ignore */` with the reason when a coverage gate is on.

## Replacing the banned constructs

| Instead of | Write |
| --- | --- |
| `any` for unknown data | `unknown`, then a zod `safeParse` at the boundary, or a type guard function |
| `await res.json()` used as a typed value | `schema.safeParse(await res.json())`; handle `success: false` with an actionable error |
| `value!` | an early return, `if (value === undefined) return ...`, or a parser that proves it |
| `x as Foo` / `x as unknown as Foo` | `satisfies Foo` (validates without widening), a guard `(x): x is Foo`, or a parsed value |
| `type Shape = { a: string }` | `interface Shape { a: string }` (`type` is for unions, intersections, mapped and conditional types) |
| `err instanceof Error ? err.message : String(err)` repeated | one shared `errorMessage(err)` helper in the project, used everywhere |
| `console.log` / `console.error` | the project logger; a browser client reports through the project's error-capture path |
| `// @ts-ignore` | fix the type; at most `// @ts-expect-error <reason>` in a type-level test |
| `a \|\| b` for a nullable left side | `a ?? b` (`||` also swallows `0`, `''`, `false`) |
| `if (x === true)` on a boolean | `if (x)` |

A real external boundary that needs a runtime-guarded cast is the one documented place for `eslint-disable-next-line <rule> -- <reason>`;
every other use is a type that is wrong at its source, and the fix is at the source.

`satisfies` keeps the narrow type and checks the shape. With `as const`, it freezes a config and still validates it:

```ts
export const ROUTES = {
    home: '/',
    projects: '/projects',
} as const satisfies Record<string, `/${string}`>;
export type RouteKey = keyof typeof ROUTES;       // 'home' | 'projects'
```

Explicit return types on every exported function (`explicit-module-boundary-types`). Let inference work for locals and for non-exported
helpers; do not annotate `const count: number = 42`.

## Unions, exhaustiveness and result codes

A state is a discriminated union, never a set of boolean flags. Exhaustiveness is checked by the compiler, not at runtime:

```ts
type Request<T> =
    | { status: 'idle' }
    | { status: 'loading' }
    | { status: 'error'; error: Error }
    | { status: 'success'; data: T };

function label<T>(state: Request<T>): string {
    switch (state.status) {
        case 'idle': return 'Idle';
        case 'loading': return 'Loading';
        case 'error': return state.error.message;
        case 'success': return 'Done';
        default: {
            const unreachable: never = state;      // a new status is a compile error here
            return unreachable;
        }
    }
}
```

For a closed set of values mapped to something (tones, variants, result codes), prefer a `Record<Union, T>`: a missing key is a compile
error and there is no `switch` to forget. Server actions and route handlers return string code unions (`'ok' | 'NOT_FOUND' | ...`)
rather than booleans or thrown errors for expected outcomes.

## Branded and nominal types

TypeScript is structural, so `UserId` and `OrderId` (both `string`) can be swapped by mistake. A brand needs a cast, which
`no-unsafe-type-assertion` rejects, so mint brands where the value is validated:

```ts
const userIdSchema = z.string().startsWith('usr_').brand<'UserId'>();
export type UserId = z.infer<typeof userIdSchema>;
export const parseUserId = (raw: unknown): UserId | null => {
    const parsed = userIdSchema.safeParse(raw);
    return parsed.success ? parsed.data : null;
};
```

Use a brand only where a swap is a realistic bug (ids across tables, cents versus whole currency units, milliseconds versus seconds).
Plain `string` ids scoped by the query's user predicate, plus named unit constants, are often enough; do not add brands everywhere for
style.

## Generics, mapped, conditional and template types

- Constrain generics (`<T, K extends keyof T>(obj: T, key: K): T[K]`); a type-parameter default is fine for a type, but never give a
  runtime parameter or option a default a caller can forget (see `idioms.md`).
- Mapped types with key remapping derive shapes from one source: ``{ [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K] }``.
- Conditional types with `infer` extract parts (`T extends Promise<infer U> ? U : T`); wrap in a tuple (`[T] extends [string]`) to stop
  distribution over a union. Prefer the built-ins (`Awaited`, `ReturnType`, `Parameters`, `Pick`, `Omit`, `Record`, `Extract`, `Exclude`)
  before writing your own, and never re-declare a built-in under its own name.
- Template literal types constrain strings (`` `/${string}` `` for a route, `` `${'click' | 'focus'}.${string}` `` for an event name).
- Variance annotations (`in`, `out`) belong in library-grade shared types only. Keep type-level programming to what removes a runtime check
  or a class of bug; a clever type nobody can read is a cost.
- Type-level tests use `// @ts-expect-error <reason>` on the line that must fail to compile.
- Barrels (`index.ts`) only at package boundaries, never inside a feature folder (circular imports). Static top-level imports; a dynamic
  `await import()` inside a function needs a comment naming the circular-dependency reason.

## Async and errors

See `idioms.md` (error values, throws with a cause, after-response hooks, `AbortSignal.timeout`). Early returns over nested conditionals.
Removing code is a valid fix.

## Constants and magic values

Security, abuse and multi-use numbers are named constants (`LIMITS.MAX_UPLOAD_SIZE`, a shared module of millisecond spans); a rate limit
is always named. A single-use field length (`z.string().max(255)`) stays inline. Map a closed value set with `as const` objects or
unions, not scattered string literals.

## Regex

Named capture groups for any group used by name (`/(?<year>\d{4})/`); the `v` flag for new patterns when the target allows; never parse
JSON, HTML, XML or SQL with a regex; a pattern over 30 characters gets a one-line comment; repeated patterns go to shared validation
helpers.
