---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---
Review this Python code:

```python
import requests

async def fetch_all(urls, results=[]):
    for url in urls:
        r = requests.get(url)
        results.append(r.text)
    return results
```
