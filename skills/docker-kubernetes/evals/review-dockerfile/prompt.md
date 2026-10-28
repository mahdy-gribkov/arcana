---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---
Review this Dockerfile for a Node API:

```dockerfile
FROM node:latest
WORKDIR /app
COPY . .
RUN npm install
ENV DB_PASSWORD=hunter2
EXPOSE 3000
CMD ["node", "index.js"]
```
