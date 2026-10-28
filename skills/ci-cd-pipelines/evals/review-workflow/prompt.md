---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---
Review this GitHub Actions workflow:

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@main
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm install
      - run: npm test
      - run: echo "Deploying with $DEPLOY_TOKEN"
        env:
          DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
```
