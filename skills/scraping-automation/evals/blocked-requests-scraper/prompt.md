---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---
My Python script gets 403 and empty pages from a product listing site that renders prices with JavaScript. Rewrite it with Playwright so it collects title and price for every product on all pages.

```python
import requests
from bs4 import BeautifulSoup

for page in range(1, 20):
    html = requests.get(f"https://shop.example.com/products?page={page}").text
    soup = BeautifulSoup(html, "html.parser")
    for card in soup.select(".product-card"):
        print(card.select_one(".title").text, card.select_one(".price").text)
```
