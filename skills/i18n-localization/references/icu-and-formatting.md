# ICU messages and locale formatting

## ICU MessageFormat

Plural rules differ per language. English has two forms (one, other). Arabic has six (zero, one, two, few, many, other). Hebrew has three (one, two, other). Never build a sentence with a ternary on the count.

**BAD: string concatenation**
```typescript
const message = count === 1 ? `You have ${count} message` : `You have ${count} messages`;
const greeting = gender === 'male' ? `Welcome, Mr. ${name}` : `Welcome, Ms. ${name}`;
```

**GOOD: ICU MessageFormat in the message file**
```json
{
  "messages": {
    "count": "{count, plural, =0 {No messages} one {# message} other {# messages}}"
  },
  "greeting": {
    "formal": "{gender, select, male {Welcome, Mr. {name}} female {Welcome, Ms. {name}} other {Welcome, {name}}}"
  },
  "cart": {
    "items": "{itemCount, plural, =0 {Your cart is empty} one {# item in cart} other {# items in cart}}",
    "total": "{total, number, ::currency/USD}"
  }
}
```

Rules:
- Always include `other`. It is required.
- Use `#` for the formatted number inside a plural branch.
- A translator may need other categories (`few`, `many`). Do not remove them from their file.
- Keep the whole sentence in one message. Do not split it across keys.

```typescript
// react-intl
import { useIntl } from 'react-intl';

function MessageCount({ count }: { count: number }) {
  const intl = useIntl();
  return <p>{intl.formatMessage({ id: 'messages.count' }, { count })}</p>;
}
```

## Rich text

```json
{ "terms": "By signing up, you agree to our <link>Terms of Service</link>" }
```

```tsx
import { useTranslations } from 'next-intl';
import Link from 'next/link';

function SignupForm() {
  const t = useTranslations('auth');
  return (
    <p>
      {t.rich('terms', { link: (chunks) => <Link href="/terms">{chunks}</Link> })}
    </p>
  );
}
```

Never put HTML strings in messages and render them with `dangerouslySetInnerHTML`.

## Dates, numbers, currency

**BAD: hardcoded formats**
```typescript
const date = new Date().toLocaleDateString('en-US');
const price = `$${amount.toFixed(2)}`;
const percent = `${(value * 100).toFixed(1)}%`;
```

**GOOD: Intl formatters tied to the active locale**
```typescript
import { useIntl } from 'react-intl';

function ProductCard({ price, date, discount }: Props) {
  const intl = useIntl();

  const formattedDate = intl.formatDate(date, { year: 'numeric', month: 'long', day: 'numeric' });
  const formattedPrice = intl.formatNumber(price, { style: 'currency', currency: 'USD' });
  const formattedDiscount = intl.formatNumber(discount, {
    style: 'percent',
    minimumFractionDigits: 0,
    maximumFractionDigits: 1
  });

  return (
    <div>
      <p>{formattedPrice}</p>
      <p>{formattedDiscount} off</p>
      <time dateTime={new Date(date).toISOString()}>{formattedDate}</time>
    </div>
  );
}
```

With next-intl the same calls are `useFormatter()` (`format.dateTime`, `format.number`, `format.relativeTime`).

Plain Intl works everywhere:

```typescript
const dateFormatter = new Intl.DateTimeFormat('es-ES', { dateStyle: 'full', timeStyle: 'short' });
const numberFormatter = new Intl.NumberFormat('de-DE', { style: 'decimal', minimumFractionDigits: 2 });

dateFormatter.format(new Date()); // "domingo, 2 de marzo de 2026, 14:30"
numberFormatter.format(1234.5);   // "1.234,50"
```

Notes:
- The currency is data (what the price is in), not a function of the locale. A German user can see a USD price.
- Pass an explicit `timeZone` for server-rendered dates. Otherwise server and browser output can differ and cause a hydration mismatch.
- Sort user-visible lists with `Intl.Collator(locale)`, not the default `sort()`.
- Use `Intl.RelativeTimeFormat` and `Intl.ListFormat` instead of hand-built "3 days ago" and "a, b and c".
