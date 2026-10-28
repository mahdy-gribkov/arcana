---
type: llm
---
PASS: Flags the latest tag and asks for a pinned slim or alpine base image.
PASS: Flags that the container runs as root and asks for a non-root USER.
PASS: Asks to copy package files first so the dependency layer is cached, and to use npm ci.
PASS: Flags the secret in ENV and says to inject it at runtime.
PASS: Suggests a multi-stage build and a .dockerignore file.
FAIL: Approves the Dockerfile or only comments on formatting.
