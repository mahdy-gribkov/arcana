---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---
I am writing renameProject(projectId, name). It can fail because the project is missing, the name is taken, or the database is down. How should I shape what it returns and throws?
