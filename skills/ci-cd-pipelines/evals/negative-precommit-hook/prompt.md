---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---
Write a bash pre-commit hook that blocks a commit when any staged file contains the text TODO or FIXME, and prints which files matched.
