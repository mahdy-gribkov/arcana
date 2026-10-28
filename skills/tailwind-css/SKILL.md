---
name: tailwind-css
description: Writes and reviews Tailwind CSS v4 code with the CSS-first setup (@import, @theme, @utility, @plugin, @source), the cn() class merge helper, mobile-first responsive design, class-based dark mode, built-in container queries, and variant-driven components. Also migrates v3 projects to v4. Use when styling with Tailwind, fixing classes that do not apply or conflict, setting up or upgrading Tailwind, adding design tokens or dark mode, or building reusable Tailwind components.
user-invocable: true
---

# Tailwind CSS Skill

This skill targets Tailwind CSS v4. In v4 the configuration lives in CSS, not in `tailwind.config.ts`. If the project still has a `tailwind.config.*` file, it is on v3 or it loads the file with `@config`. Check `package.json` before you choose syntax.

Longer examples: [references/components.md](references/components.md) (variant components and form inputs) and [references/v3-to-v4.md](references/v3-to-v4.md) (migration and renamed utilities).

## Core Configuration (v4)

**BAD: v3 directives and a JS config for tokens**
```css
/* styles/globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;
```
```ts
// tailwind.config.ts
export default {
  content: ['./src/**/*.{js,ts,jsx,tsx}'],
  theme: { extend: { colors: { brand: { 500: '#3b82f6' } } } },
};
```

**GOOD: one CSS file, tokens in @theme**
```css
/* styles/globals.css */
@import "tailwindcss";

@theme {
  --color-brand-50: oklch(0.97 0.02 240);
  --color-brand-500: oklch(0.62 0.19 260);
  --color-brand-900: oklch(0.3 0.1 265);
  --font-display: "Inter", sans-serif;
  --breakpoint-xs: 475px;
}
```

Every `@theme` variable in a utility namespace becomes a utility (`bg-brand-500`, `font-display`, `xs:flex`) and a CSS variable (`var(--color-brand-500)`). Spacing needs no tokens: `p-18` works because spacing is a multiple of one base unit. Do not mix inline `style={{}}` with Tailwind for values the tokens already cover.

Install (build tool plugin, no `content` array needed):
```bash
npm install tailwindcss @tailwindcss/vite     # Vite
npm install tailwindcss @tailwindcss/postcss  # Next.js and other PostCSS setups
```

## cn() Utility Pattern

**BAD: string concatenation, conflicting classes are not resolved**
```tsx
export function Card({ className }: { className?: string }) {
  // p-4 and p-8 both apply, and CSS source order decides the winner
  return <div className={`p-4 rounded-lg bg-white ${className}`} />;
}
// <Card className="p-8 bg-blue-50" />
```

**GOOD: clsx plus tailwind-merge, the last class wins**
```tsx
// lib/cn.ts
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// components/Card.tsx
import { cn } from '@/lib/cn';

interface CardProps {
  className?: string;
  variant?: 'default' | 'outlined';
}

export function Card({ className, variant = 'default' }: CardProps) {
  return (
    <div
      className={cn(
        'p-4 rounded-lg',
        variant === 'default' && 'bg-white shadow-sm',
        variant === 'outlined' && 'border border-gray-300',
        className
      )}
    />
  );
}
// <Card className="p-8 bg-blue-50" /> => p-8 and bg-blue-50 override correctly
```

## Responsive Design Patterns

Unprefixed classes are the mobile base. Each prefix (`sm:`, `md:`, `lg:`) means "from this width up".

**BAD: desktop-first thinking, the base class is overridden by nothing**
```tsx
<div className="grid-cols-4 md:grid-cols-2 sm:grid-cols-1" />
```

**GOOD: mobile-first progressive enhancement**
```tsx
<div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4" />
```

Add or change breakpoints with `--breakpoint-*` in `@theme` (see Core Configuration). Use `max-md:` only for a rule that must stop at a width.

## Dark Mode Implementation

In v4 the `dark:` variant follows `prefers-color-scheme` by default. For a manual toggle, override the variant in CSS.

**BAD: branching class strings in JS**
```tsx
<div className={isDark ? 'bg-gray-900 text-white' : 'bg-white text-gray-900'} />
```

**GOOD: dark: variants, with a class-based switch when you need a toggle**
```css
@import "tailwindcss";
@custom-variant dark (&:where(.dark, .dark *));
```
```tsx
<div className="bg-white text-gray-900 dark:bg-gray-900 dark:text-white">Content</div>
```

Put or remove the `dark` class on `<html>` from a small script or a theme library, and add `suppressHydrationWarning` to `<html>` if the class is set before hydration. Do not hardcode `className="dark"` in the layout: that locks dark mode on.

## Custom Utilities and Plugins

**BAD: the same long class list copied across the code**
```tsx
<div className="backdrop-blur-md bg-white/10 border border-white/20 rounded-lg" />
// repeated in 20 places
```

**GOOD: @utility for a reusable rule, @plugin for a package plugin**
```css
@import "tailwindcss";
@plugin "@tailwindcss/typography";
@plugin "@tailwindcss/forms";

@utility glass {
  backdrop-filter: blur(12px);
  background-color: rgb(255 255 255 / 0.1);
  border: 1px solid rgb(255 255 255 / 0.2);
}
```
```tsx
<div className="glass rounded-lg shadow-xl">Content</div>
```

A custom `@utility` works with every variant (`hover:glass`, `md:glass`). To keep an existing JS plugin or config, load it with `@config "../tailwind.config.ts";` or `@plugin "./my-plugin.js";`.

## Anti-Pattern: @apply Overuse

**BAD: a CSS file full of @apply**
```css
.button { @apply px-4 py-2 bg-blue-500 text-white rounded-sm hover:bg-blue-600; }
.card   { @apply p-6 bg-white rounded-lg shadow-md; }
.input  { @apply w-full px-3 py-2 border border-gray-300 rounded-sm; }
/* Loses composability and duplicates what a component does better */
```

**GOOD: a component that owns its classes**

Wrap the classes in a component and use `cva` for variants. The full `Button` and `Input` examples are in [references/components.md](references/components.md). Use `@apply` only for styles you cannot put in markup, such as third-party HTML you do not control.

## Animation Utilities

**BAD: a loose keyframe and class that bypass the theme**
```css
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
.fade-in { animation: fadeIn 0.5s ease-in; }
```

**GOOD: keyframes and the animation token inside @theme**
```css
@theme {
  --animate-fade-in: fade-in 0.5s ease-out;
  --animate-shimmer: shimmer 2s infinite linear;

  @keyframes fade-in {
    0% { opacity: 0; transform: translateY(10px); }
    100% { opacity: 1; transform: translateY(0); }
  }
  @keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
  }
}
```
```tsx
<div className="animate-fade-in motion-reduce:animate-none">Content</div>
```

Always pair motion with `motion-reduce:` so users who ask for less motion get none.

## Performance: Content Detection and Dynamic Classes

v4 finds source files on its own. It respects `.gitignore` and skips `node_modules` and binary files. You do not write a `content` array.

**BAD: building class names from fragments**
```tsx
// Tailwind scans text, so it never sees "bg-red-500" here
<div className={`bg-${color}-500`} />
```

**GOOD: complete class names in a lookup, and @source for extra paths**
```tsx
const colorMap = {
  error: 'bg-red-500',
  success: 'bg-green-500',
  info: 'bg-blue-500',
} as const;

export function Alert({ type }: { type: keyof typeof colorMap }) {
  return <div className={colorMap[type]}>Alert</div>;
}
```
```css
@import "tailwindcss";
@source "../node_modules/@my-company/ui";            /* a package that is ignored by default */
@source inline("bg-{red,green,blue}-{400,500,600}"); /* classes that only exist at runtime (v4.1+) */
```

## Container Queries

Container queries are built in to v4. No plugin is needed.

**BAD: viewport breakpoints for a component that lives in a narrow sidebar**
```tsx
<div className="p-4 md:p-6 lg:p-8">
  <h2 className="text-lg md:text-xl lg:text-2xl">Title</h2>
</div>
```

**GOOD: the component responds to its own container**
```tsx
<div className="@container">
  <div className="p-4 @md:p-6 @lg:p-8">
    <h2 className="text-lg @md:text-xl @lg:text-2xl">Title</h2>
  </div>
</div>
```

## Arbitrary Values and CSS Variables

**BAD: magic numbers in class names**
```tsx
<section className="h-[calc(100vh-64px)] pt-[72px]">Content</section>
```

**GOOD: named variables, referenced with the shorthand**
```css
@theme {
  --header-height: 4rem;
  --content-padding: 4.5rem;
}
```
```tsx
<section className="h-[calc(100vh-var(--header-height))] pt-(--content-padding)">Content</section>
```

`pt-(--content-padding)` is the v4 shorthand for `pt-[var(--content-padding)]`.

## Focus States

Keep a visible focus indicator. In v4, `outline-none` removes the outline completely. Use `outline-hidden` when you replace it with a ring, and prefer `focus-visible:` so the ring shows for keyboard users.

**BAD: focus removed and nothing replaces it**
```tsx
<input className="focus:outline-none" />
```

**GOOD: the ring replaces the outline**
```tsx
<input className="rounded-lg border px-3 py-2 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-blue-500" />
```

## Workflow: Apply This Skill

1. **Check the version**: read `package.json` and look for `tailwind.config.*` and `@tailwind` directives. Use v3 syntax only when the project is on v3.
2. **Audit className usage**: find string concatenation that should use `cn()`.
3. **Check @apply usage**: replace it with components or `@utility`.
4. **Verify tokens**: colors, spacing and breakpoints live in `@theme`, not in magic values.
5. **Test dark mode**: confirm `dark:` variants work and the toggle (if any) sets the `dark` class.
6. **Review responsive design**: mobile-first, container queries for reusable components.
7. **Check dynamic classes**: complete class names only, or `@source inline(...)`.
8. **Build**: run the project build and check the CSS size.

## Common Fixes

**Fix: Tailwind classes not applying**
- Confirm the CSS file has `@import "tailwindcss";` and is imported once by the app.
- Confirm the build plugin (`@tailwindcss/vite` or `@tailwindcss/postcss`) is installed and registered.
- If the file lives in an ignored path (`node_modules`, `.gitignore`), add `@source`.
- Clear the framework cache, for example delete the `.next` folder.
- Check for specificity: a later or more specific rule can override the utility.

**Fix: Dynamic classes not working**
- Use complete class strings in a lookup object, never `text-${color}-500`.
- For classes that only exist at runtime, use `@source inline(...)`.

**Fix: Dark mode not switching**
- Default is `prefers-color-scheme`. For a toggle, add the `@custom-variant dark` line.
- Check the `<html>` element actually gets the `dark` class.
- Check the `dark:` variants sit on the affected elements.
