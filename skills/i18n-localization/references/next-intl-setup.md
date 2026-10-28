# next-intl setup for Next.js 16

Routing, request config, layouts, locale switching, dynamic loading, and typed messages. Written for next-intl 4.x. Check the installed version before copying: the API changed between 3.x and 4.x.

## Routing config (one source of truth)

```typescript
// src/i18n/routing.ts
import { defineRouting } from 'next-intl/routing';

export const routing = defineRouting({
  locales: ['en', 'he', 'ar', 'es'],
  defaultLocale: 'en',
  localePrefix: 'as-needed' // /about for en, /he/about for Hebrew
});
```

```typescript
// src/i18n/navigation.ts
// Locale-aware wrappers around next/link and next/navigation.
import { createNavigation } from 'next-intl/navigation';
import { routing } from './routing';

export const { Link, redirect, usePathname, useRouter, getPathname } =
  createNavigation(routing);
```

## proxy.ts (middleware.ts before Next.js 16)

```typescript
// src/proxy.ts
import createMiddleware from 'next-intl/middleware';
import { routing } from './i18n/routing';

export default createMiddleware(routing);

export const config = {
  // Skip api, trpc, _next, _vercel and paths with a dot (favicon.ico)
  matcher: '/((?!api|trpc|_next|_vercel|.*\\..*).*)'
};
```

On Next.js 15 and older, name the file `middleware.ts`. The code is the same.

## Request config

```typescript
// src/i18n/request.ts
import { hasLocale } from 'next-intl';
import { getRequestConfig } from 'next-intl/server';
import { routing } from './routing';

export default getRequestConfig(async ({ requestLocale }) => {
  const requested = await requestLocale;
  const locale = hasLocale(routing.locales, requested) ? requested : routing.defaultLocale;

  return {
    locale,
    messages: (await import(`../../messages/${locale}.json`)).default
  };
});
```

Newer next-intl and Next.js versions can read the locale from `next/root-params` instead of `requestLocale`. Check the next-intl "Routing setup" page for the version you use.

## Layout

In Next.js 15 and 16, `params` is a Promise. Await it.

**BAD: synchronous params, unchecked locale, `any` cast**
```tsx
export default async function LocaleLayout({ children, params: { locale } }: Props) {
  if (!locales.includes(locale as any)) notFound();
  // ...
}
```

**GOOD: awaited params, validated locale, static rendering**
```tsx
// src/app/[locale]/layout.tsx
import { hasLocale, NextIntlClientProvider } from 'next-intl';
import { setRequestLocale } from 'next-intl/server';
import { notFound } from 'next/navigation';
import { routing } from '@/i18n/routing';
import { getDirection } from '@/i18n/direction';

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

export default async function LocaleLayout({
  children,
  params
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!hasLocale(routing.locales, locale)) notFound();
  setRequestLocale(locale); // before any next-intl call, enables static rendering

  return (
    <html lang={locale} dir={getDirection(locale)}>
      <body>
        <NextIntlClientProvider>{children}</NextIntlClientProvider>
      </body>
    </html>
  );
}
```

`NextIntlClientProvider` inherits messages and locale from the request config in next-intl 4.x. Pass only the namespaces a client subtree needs if bundle size matters.

Call `setRequestLocale(locale)` in every page and layout that should render statically.

## Pages and metadata

```tsx
// src/app/[locale]/about/page.tsx
import { getTranslations, setRequestLocale } from 'next-intl/server';

type Props = { params: Promise<{ locale: string }> };

export async function generateMetadata({ params }: Props) {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: 'about' });
  return { title: t('metaTitle'), description: t('metaDescription') };
}

export default async function AboutPage({ params }: Props) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('about');
  return <h1>{t('title')}</h1>;
}
```

In a non-async Server Component or a Client Component, use the `useTranslations` hook.

## Locale switcher

**BAD: cookie by hand, then refresh**
```tsx
document.cookie = `locale=${locale}`;
router.refresh();
```

**GOOD: locale-aware router from createNavigation**
```tsx
'use client';
import { useLocale, useTranslations } from 'next-intl';
import { usePathname, useRouter } from '@/i18n/navigation';
import { routing } from '@/i18n/routing';

export function LocaleSwitcher() {
  const t = useTranslations('common');
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();

  return (
    <select
      value={locale}
      onChange={(event) => router.replace(pathname, { locale: event.target.value })}
      aria-label={t('selectLanguage')}
    >
      {routing.locales.map((code) => (
        <option key={code} value={code} lang={code}>
          {t(`locales.${code}`)}
        </option>
      ))}
    </select>
  );
}
```

Show each language in its own name ("Espanol", not "Spanish") and set `lang` on each option so screen readers pronounce it.

Locale detection (`Accept-Language` and a cookie) is on by default in the proxy. Turn it off with `localeDetection: false` in `defineRouting` if you need stable URLs only.

## Loading messages

**BAD: import every locale into the bundle**
```typescript
import en from './messages/en.json';
import he from './messages/he.json';
const messages = { en, he };
```

**GOOD: import only the active locale, merge namespaces when files are large**
```typescript
// src/i18n/request.ts, inside getRequestConfig
const [common, home] = await Promise.all([
  import(`../../messages/${locale}/common.json`),
  import(`../../messages/${locale}/home.json`)
]);
return { locale, messages: { common: common.default, home: home.default } };
```

Do not swallow a failed import and fall back silently. A missing file for a configured locale is a build error. Fix the file. If you need a fallback for partly translated locales, merge the default-locale messages under the active ones and log the missing keys at build time.

## Typed messages

Typos in keys should fail the type check, not production.

```typescript
// global.ts
import { routing } from '@/i18n/routing';
import messages from './messages/en.json';

declare module 'next-intl' {
  interface AppConfig {
    Locale: (typeof routing.locales)[number];
    Messages: typeof messages;
  }
}
```

With this in place, `t('titel')` is a type error and keys autocomplete. In next-intl 3.x the equivalent was `interface IntlMessages`. Treat the source-language file as the type, and check other locales against it with a test (same keys, same ICU placeholders).
