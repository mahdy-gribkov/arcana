---
type: llm
---
PASS: Uses Playwright with a browser context and waits for the rendered elements instead of fixed sleeps or networkidle.
PASS: Handles pagination by following the next control or detecting the end, with a page limit.
PASS: Adds a delay or rate limit between requests, retries with backoff, and respects robots.txt and the site terms.
FAIL: Only changes the User-Agent header on requests, or hardcodes proxy credentials in the source.
