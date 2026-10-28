---
name: i18n-localization
description: "Internationalize and localize web applications with next-intl, react-intl, ICU MessageFormat, RTL layouts, locale routing, and dynamic locale loading. Use when adding translations or a new language, writing plural or select messages, supporting Hebrew or Arabic RTL, formatting dates, numbers, or currency per locale, or when the user mentions i18n, l10n, next-intl, or locale files."
user-invocable: true
---

# i18n-localization

Internationalization (i18n) and localization (l10n) for web applications. Implements proper message formatting, locale routing, RTL support, and dynamic translation loading.

## Where to look

| Task | Read |
|---|---|
| next-intl routing, proxy.ts, layouts, locale switcher, loading messages, typed keys | [references/next-intl-setup.md](references/next-intl-setup.md) |
| ICU plural and select, rich text, dates, numbers, currency | [references/icu-and-formatting.md](references/icu-and-formatting.md) |
| Hebrew, Arabic, or other RTL layouts, logical CSS, Tailwind | [references/rtl-layout.md](references/rtl-layout.md) |

Read the file that matches the task before writing code. The core rules below always apply.

## Core rules

1. **No user-visible string in code.** Every label, error, placeholder, `aria-label`, and page title comes from a message file.
2. **One message per sentence.** Never concatenate fragments or build plurals with a ternary. Use ICU `plural` and `select`.
3. **Always include the `other` branch** in plural and select messages.
4. **Format with Intl.** Dates, numbers, currency, lists, and relative times go through `Intl` or the library formatter, never `toFixed` or a hardcoded pattern.
5. **Logical CSS only.** Use `margin-inline-start`, `text-align: start`, and Tailwind `ms-*`/`pe-*`. Never `left` or `right` for layout.
6. **Set `lang` and `dir` on `<html>`** from the active locale. Cover `he`, `ar`, `fa`, and `ur` as RTL.
7. **Validate the locale at the boundary** (route segment, cookie, header) against the configured list. Unknown locale means 404 or the default, never a thrown import error.
8. **Load only the active locale.** No static imports of every message file.
9. **Keep locale files in sync.** Same keys and same ICU placeholders in every language. Fail CI when they drift.
10. **Do not translate by machine and ship unreviewed.** Mark machine drafts and have a native speaker review user-facing copy.

## Translation file structure

**BAD: flat keys, mixed namespaces, layout in the name**
```json
{
  "welcomeMessage": "Welcome",
  "homePageTitle": "Home",
  "userProfileName": "Name",
  "checkoutButtonSubmit": "Submit Order"
}
```

**GOOD: namespaced by feature, nested by meaning**
```json
// messages/en/common.json
{ "welcome": "Welcome", "loading": "Loading...", "error": "An error occurred" }

// messages/en/home.json
{ "title": "Home", "hero": { "heading": "Welcome to our platform", "subheading": "Build amazing things" } }

// messages/en/user.json
{ "profile": { "name": "Name", "email": "Email", "updatedAt": "Last updated {date}" } }
```

Name keys for what the text means (`checkout.submit`), not where it sits or what it says. Keep the source-language file as the reference and the type source.

## Plurals in one line

**BAD**
```typescript
const message = count === 1 ? `You have ${count} message` : `You have ${count} messages`;
```

**GOOD**
```json
{ "count": "{count, plural, =0 {No messages} one {# message} other {# messages}}" }
```

More ICU, rich text, and Intl formatting in [references/icu-and-formatting.md](references/icu-and-formatting.md).

## Logical CSS in one line

**BAD**
```css
.sidebar { float: left; margin-right: 20px; text-align: left; }
```

**GOOD**
```css
.sidebar { float: inline-start; margin-inline-end: 20px; text-align: start; }
```

Direction handling, icon mirroring, and mixed LTR/RTL text in [references/rtl-layout.md](references/rtl-layout.md).

## Next.js 16 with next-intl in one screen

- `defineRouting({ locales, defaultLocale })` in `src/i18n/routing.ts` is the single source of locales.
- `src/proxy.ts` runs `createMiddleware(routing)`. Before Next.js 16 the file is `middleware.ts`.
- `src/i18n/request.ts` uses `getRequestConfig` and validates the locale with `hasLocale`.
- `app/[locale]/layout.tsx` awaits `params` (a Promise in Next.js 15 and 16), calls `notFound()` for bad locales, calls `setRequestLocale(locale)`, and sets `lang` and `dir`.
- Use `createNavigation(routing)` wrappers (`Link`, `useRouter`, `usePathname`) so links keep the locale.
- Type message keys by augmenting `AppConfig` in `next-intl`.

Full code in [references/next-intl-setup.md](references/next-intl-setup.md).

## Review checklist

- [ ] No hardcoded visible strings, including `alt`, `title`, `placeholder`, and `aria-label`
- [ ] Plurals and selects use ICU with `other`
- [ ] Dates, numbers, and currency use Intl with an explicit time zone on the server
- [ ] No `left`, `right`, `ml-*`, `mr-*`, `text-left` in layout code
- [ ] `lang` and `dir` set from the locale; Hebrew and Arabic both covered
- [ ] `hreflang` alternates and a locale-aware sitemap for public pages
- [ ] Every locale has the same keys as the source file
- [ ] Locale switcher shows each language in its own name and sets `lang` on options
