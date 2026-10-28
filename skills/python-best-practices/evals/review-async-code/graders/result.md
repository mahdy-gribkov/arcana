---
type: llm
---
PASS: Flags blocking requests.get inside an async function and recommends httpx.AsyncClient or asyncio.to_thread.
PASS: Flags the mutable default argument results=[].
PASS: Asks for type hints on the parameters and the return value.
PASS: Suggests running the requests concurrently with asyncio.gather or a TaskGroup, with a timeout set.
FAIL: Approves the function or only comments on naming.
