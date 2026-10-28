---
type: llm
---
PASS: Uses a src layout with a tests directory.
PASS: Puts the configuration in pyproject.toml, including ruff and a strict type checker such as mypy or pyright.
PASS: Uses uv for the environment and lockfile, with dev tools in a dev dependency group.
PASS: Defines a console script entry point under project.scripts.
FAIL: Uses a flat layout with requirements.txt and setup.py only.
