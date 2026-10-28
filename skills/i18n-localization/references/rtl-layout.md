# RTL layout support (Hebrew, Arabic, Persian, Urdu)

## Direction from the locale

Derive `dir` in one place and use it on `<html>`.

```typescript
// src/i18n/direction.ts
const RIGHT_TO_LEFT_LANGUAGES = new Set(['ar', 'he', 'fa', 'ur']);

export function getDirection(locale: string): 'rtl' | 'ltr' {
  const language = locale.split('-')[0] ?? locale;
  return RIGHT_TO_LEFT_LANGUAGES.has(language) ? 'rtl' : 'ltr';
}
```

**BAD: only one language checked**
```tsx
<html lang={locale} dir={locale === 'ar' ? 'rtl' : 'ltr'}>
```

**GOOD**
```tsx
<html lang={locale} dir={getDirection(locale)}>
```

## Logical CSS properties

**BAD: hardcoded left and right**
```css
.sidebar {
  float: left;
  margin-right: 20px;
  text-align: left;
}

.arrow {
  padding-left: 10px;
}
```

**GOOD: logical properties flip with `dir`**
```css
.sidebar {
  float: inline-start;
  margin-inline-end: 20px;
  text-align: start;
}

.arrow {
  padding-inline-start: 10px;
}
```

Other logical pairs: `inset-inline-start` (left), `border-inline-end`, `padding-block`, `margin-block`.

## Tailwind

Tailwind CSS v3.3+ and v4 ship logical utilities. No plugin is needed.

```html
<div class="ms-4 me-2 ps-4 pe-2 text-start border-s">...</div>
<div class="start-0">...</div> <!-- inset-inline-start -->
```

Use `rtl:` and `ltr:` variants only for the cases logical utilities cannot express:

```html
<svg class="rtl:-scale-x-100">...</svg> <!-- mirror a directional arrow icon -->
```

## What to flip and what not to

- Flip: layout order, arrows and chevrons that mean "next" or "back", progress bars, sliders, carousels.
- Do not flip: logos, photos, clocks, play buttons, checkmarks, phone numbers, code blocks, charts with a time axis (follow local convention).
- Mixed content: wrap embedded LTR text (an email, URL, code, or Latin brand name) in `<bdi>` or set `dir="ltr"` on that span, so punctuation does not jump to the wrong side.
- Form inputs for emails, URLs, and phone numbers: `dir="ltr"` even on an RTL page.
- Numbers stay Western digits in Hebrew. Arabic locales may use Arabic-Indic digits; let `Intl.NumberFormat` decide.

## JS that reads direction

Scroll offsets, `getBoundingClientRect().left`, and `event.clientX` math are physical. Compute from `dir` or use logical APIs (`scrollIntoView({ inline: 'start' })`). Test every carousel and drawer in RTL.

## Testing

- Add an RTL locale to Playwright or Storybook projects and take screenshots of key pages.
- Use pseudo-text that is long (German) and short (Chinese) to catch overflow.
- Grep for physical properties in CSS and Tailwind classes: `margin-left`, `padding-right`, `left-`, `right-`, `ml-`, `mr-`, `pl-`, `pr-`, `text-left`, `text-right`.
