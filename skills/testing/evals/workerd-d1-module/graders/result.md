---
type: llm
---
PASS: Puts the test in a *.workerd.test.ts file that runs under the Cloudflare Workers vitest pool against real D1 through the cloudflare:test bindings.
PASS: Asserts the stored state with a SELECT (the count equals the cap and no row grows past it), not only the function return values, and uses a unique namespace per test.
FAIL: Mocks Drizzle or D1 with canned rows, or writes it as a jsdom or plain node unit test.
FAIL: Uses a bare toHaveBeenCalled() or only toBeDefined-style assertions.
