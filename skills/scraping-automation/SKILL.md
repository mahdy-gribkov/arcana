---
name: scraping-automation
description: "Build resilient web scrapers with Playwright and Puppeteer: browser contexts, rate limiting, proxy rotation, retries, structured data extraction, and respectful crawling. Use when writing or debugging a scraper, crawler, or browser automation script, extracting data from pages or APIs, handling dynamic content, selectors that break, blocked requests, or when the user mentions Playwright, Puppeteer, scraping, or crawling."
user-invocable: true
argument-hint: "[url] [--headless] [--proxy] [--stealth]"
---

# Scraping Automation Skill

Build production-grade web scrapers with anti-detection, resilient extraction, and respectful crawling patterns.

## Browser Context and Stealth Mode

**BAD:** Default browser fingerprint exposes automation.

```typescript
// Detectable as bot, no stealth configuration
const browser = await playwright.chromium.launch();
const page = await browser.newPage();
await page.goto('https://example.com');
```

**GOOD:** Stealth mode with randomized fingerprints.

```typescript
import { chromium } from 'playwright-extra';
import stealth from 'puppeteer-extra-plugin-stealth';

chromium.use(stealth());

const browser = await chromium.launch({
  headless: true,
  args: [
    '--disable-blink-features=AutomationControlled',
    '--disable-dev-shm-usage' // only needed in small containers; never add --no-sandbox on a machine you also browse with
  ]
});

const context = await browser.newContext({
  userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
  viewport: { width: 1920, height: 1080 },
  locale: 'en-US',
  timezoneId: 'America/New_York',
  permissions: ['geolocation'],
  geolocation: { latitude: 40.7128, longitude: -74.0060 },
  colorScheme: 'light'
});

const page = await context.newPage();
// Playwright discourages 'networkidle'. Wait for the element you need instead.
await page.goto('https://example.com', { waitUntil: 'domcontentloaded' });
await page.locator('h1').waitFor();
```

## Proxy Rotation and IP Management

**BAD:** Single IP for high-volume scraping triggers rate limits.

```python
# No proxy rotation, easy to block
async with async_playwright() as p:
    browser = await p.chromium.launch()
    page = await browser.new_page()
    for url in urls:
        await page.goto(url)  # Same IP for all requests
```

**GOOD:** Rotating proxies with session management.

```python
import random
from playwright.async_api import async_playwright

import json
import os

# Proxy credentials come from the environment (a JSON list), never from source code.
# PROXY_LIST='[{"server": "http://proxy1.example.com:8080", "username": "...", "password": "..."}]'
proxies = json.loads(os.environ['PROXY_LIST'])

async def scrape_with_rotation(urls):
    async with async_playwright() as p:
        for url in urls:
            proxy = random.choice(proxies)
            browser = await p.chromium.launch(proxy=proxy)

            context = await browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport={'width': random.randint(1366, 1920), 'height': random.randint(768, 1080)}
            )

            page = await context.new_page()
            try:
                await page.goto(url, timeout=30000)
                data = await extract_data(page)
                yield data
            finally:
                await browser.close()
```

## Resilient Selectors with Fallbacks

**BAD:** Hardcoded selectors break when page structure changes.

```typescript
// Brittle, fails if class names change
const title = await page.locator('.product-title-v2').textContent();
const price = await page.locator('#price_123').textContent();
```

**GOOD:** Multiple selector strategies with fallback chain.

```typescript
async function extractWithFallback(page, selectors) {
  for (const selector of selectors) {
    try {
      const element = page.locator(selector);
      if (await element.count() > 0) {
        return await element.first().textContent();
      }
    } catch (e) {
      continue;
    }
  }
  return null;
}

const title = await extractWithFallback(page, [
  'h1[data-testid="product-title"]',
  '.product-title',
  'h1.title',
  '//h1[contains(@class, "product")]'
]);

const price = await extractWithFallback(page, [
  '[data-price]',
  '.price-current',
  'span:has-text("$")',
  '//span[contains(text(), "$")]'
]);
```

## Structured Data Extraction Pipeline

**BAD:** Inline extraction logic duplicated across scrapers.

```typescript
const products = [];
const items = await page.locator('.product-card').all();
for (const item of items) {
  products.push({
    title: await item.locator('.title').textContent(),
    price: await item.locator('.price').textContent()
  });
}
```

**GOOD:** Reusable extraction schema with validation.

```typescript
interface ExtractionSchema {
  fields: {
    [key: string]: {
      selectors: string[];
      transform?: (val: string) => any;
      required?: boolean;
    };
  };
  listSelector?: string;
}

async function extract(page, schema: ExtractionSchema) {
  const results = [];
  const containers = schema.listSelector
    ? await page.locator(schema.listSelector).all()
    : [page];

  for (const container of containers) {
    const item: any = {};

    for (const [key, config] of Object.entries(schema.fields)) {
      const value = await extractWithFallback(container, config.selectors);

      if (!value && config.required) {
        throw new Error(`Required field ${key} not found`);
      }

      item[key] = config.transform ? config.transform(value) : value;
    }

    results.push(item);
  }

  return results;
}

// Usage
const productSchema: ExtractionSchema = {
  listSelector: '.product-card',
  fields: {
    title: { selectors: ['h2.title', '.product-name'], required: true },
    price: {
      selectors: ['[data-price]', '.price'],
      transform: (v) => parseFloat(v.replace(/[^0-9.]/g, '')),
      required: true
    },
    rating: {
      selectors: ['.rating', '[data-rating]'],
      transform: (v) => parseFloat(v)
    },
    availability: { selectors: ['.stock-status', '[data-stock]'] }
  }
};

const products = await extract(page, productSchema);
```

## Pagination Handling

**BAD:** Manual URL construction misses dynamic pagination.

```typescript
// Assumes page=N pattern, breaks with AJAX pagination
for (let i = 1; i <= 10; i++) {
  await page.goto(`https://example.com/products?page=${i}`);
}
```

**GOOD:** Dynamic pagination detection with multiple strategies.

```typescript
async function scrapeAllPages(page, initialUrl, options = {}) {
  const { maxPages = 100, waitForSelector = 'body' } = options;
  const results = [];
  let currentPage = 1;

  await page.goto(initialUrl);

  while (currentPage <= maxPages) {
    await page.waitForSelector(waitForSelector);

    const pageData = await extract(page, productSchema);
    results.push(...pageData);

    // Try multiple pagination strategies
    let navigated = false;

    // Strategy 1: Next button
    const nextButton = page.locator('a:has-text("Next"), button:has-text("Next"), [aria-label="Next"]');
    if (await nextButton.count() > 0 && await nextButton.first().isEnabled()) {
      await nextButton.first().click();
      await page.waitForLoadState('domcontentloaded');
      navigated = true;
    }

    // Strategy 2: Page number links
    if (!navigated) {
      const nextPageLink = page.locator(`a:has-text("${currentPage + 1}")`);
      if (await nextPageLink.count() > 0) {
        await nextPageLink.first().click();
        await page.waitForLoadState('domcontentloaded');
        navigated = true;
      }
    }

    // Strategy 3: Infinite scroll
    if (!navigated) {
      const previousHeight = await page.evaluate(() => document.body.scrollHeight);
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
      await page.waitForTimeout(2000);
      const newHeight = await page.evaluate(() => document.body.scrollHeight);
      navigated = newHeight > previousHeight;
    }

    if (!navigated) break;
    currentPage++;
  }

  return results;
}
```

## Respectful Crawling

**BAD:** Parallel requests at full speed, no identification, ignoring the site's rules.

**GOOD:** Rules before code.

- Prefer an official API, feed, sitemap, or data export over scraping HTML.
- Read `robots.txt` and the site's terms. Do not crawl disallowed paths.
- Rate limit per host (for example one request per second or slower) and back off on 429 and 503 responses. Honor `Retry-After`.
- Do not bypass logins, paywalls, or CAPTCHAs.
- Collect only the fields you need. Personal data needs a legal basis; check the privacy law that applies to you.
- Cache responses so a retry does not hit the site again.

See references/advanced.md for extended examples.
