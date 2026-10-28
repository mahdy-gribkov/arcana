# Tailwind v3 to v4 migration

Loaded from SKILL.md. Use this when a project still has `tailwind.config.*`, `@tailwind` directives, or v3 class names.

## Run the official upgrade tool first

```bash
npx @tailwindcss/upgrade
```

It needs Node 20 or newer. Run it on a clean git branch and review the diff. It updates dependencies, converts the config to CSS and renames most utilities.

## What changes

| v3 | v4 |
| --- | --- |
| `@tailwind base; @tailwind components; @tailwind utilities;` | `@import "tailwindcss";` |
| `tailwind.config.ts` with `theme.extend` | `@theme { --color-*: ...; }` in CSS (or `@config` to keep the file) |
| `content: [...]` | Automatic detection, `@source "path"` for extra paths |
| `safelist: [...]` | `@source inline("...")` (v4.1 and newer) |
| `plugins: [require('@tailwindcss/forms')]` | `@plugin "@tailwindcss/forms";` |
| `addUtilities(...)` in a JS plugin | `@utility name { ... }` |
| `darkMode: 'class'` | `@custom-variant dark (&:where(.dark, .dark *));` |
| `@tailwindcss/container-queries` plugin | Built in (`@container`, `@md:`) |
| `postcss-import` and `autoprefixer` | Not needed with `@tailwindcss/postcss` |
| `tailwindcss` as the PostCSS plugin | `@tailwindcss/postcss` (or `@tailwindcss/vite`) |

## Renamed utilities

| v3 | v4 |
| --- | --- |
| `shadow-sm` / `shadow` | `shadow-xs` / `shadow-sm` |
| `rounded-sm` / `rounded` | `rounded-xs` / `rounded-sm` |
| `blur-sm` / `blur` | `blur-xs` / `blur-sm` |
| `outline-none` | `outline-hidden` (v4 `outline-none` removes the outline fully) |
| `ring` (3px) | `ring-3` (v4 `ring` is 1px) |
| `bg-opacity-50` and similar | `bg-black/50` |
| `flex-shrink-0`, `flex-grow` | `shrink-0`, `grow` |
| `bg-gradient-to-r` | `bg-linear-to-r` (use the new name; v4 also adds `bg-linear-<angle>`) |

## Behavior changes to check by hand

- Default border and divide color is `currentColor`, not `gray-200`. Add an explicit border color where you relied on the default.
- Buttons use `cursor: default`, not `pointer`. Add `cursor-pointer` where you want it.
- Variants stack left to right in v4 (`*:first:pt-0`), the reverse of v3.
- The important modifier goes at the end: `bg-red-500!`.
- Arbitrary CSS variable values use parentheses: `bg-(--brand)` instead of `bg-[--brand]`.
- Default colors use `oklch`, so a few shades look slightly different on wide-gamut screens.
- Browser floor: Safari 16.4, Chrome 111, Firefox 128. Use v3.4 if you must support older browsers.
