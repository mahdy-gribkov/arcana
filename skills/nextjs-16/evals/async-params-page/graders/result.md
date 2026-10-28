---
type: llm
---
PASS: Types params as a Promise and awaits it in both the page and generateMetadata.
PASS: Handles the missing post case (notFound or a null check) instead of reading post.title unguarded.
FAIL: Leaves params synchronous or suggests downgrading Next.js.
