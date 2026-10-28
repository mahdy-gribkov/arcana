---
type: llm
---
PASS: Says to use a real img element, not a CSS background, so the browser can discover the LCP image early.
PASS: Says to remove lazy loading from the LCP image and set fetchpriority high or preload it.
PASS: Recommends modern formats (AVIF or WebP) and responsive srcset and sizes, with explicit width and height.
FAIL: Only suggests minifying JavaScript or upgrading the server.
