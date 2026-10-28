# Tailwind components: variants and form inputs

Loaded from SKILL.md. Examples use Tailwind v4 class names and the `cn()` helper from `lib/cn.ts`.

## Variant component with cva

```bash
npm install class-variance-authority clsx tailwind-merge
```

```tsx
// components/ui/Button.tsx
import { cn } from '@/lib/cn';
import { type VariantProps, cva } from 'class-variance-authority';

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-lg font-medium transition-colors focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-blue-500 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'bg-blue-500 text-white hover:bg-blue-600',
        outline: 'border border-gray-300 bg-transparent hover:bg-gray-100',
        ghost: 'hover:bg-gray-100',
      },
      size: {
        sm: 'h-9 px-3 text-sm',
        md: 'h-10 px-4',
        lg: 'h-11 px-8',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
    },
  }
);

interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export function Button({ className, variant, size, ...props }: ButtonProps) {
  return (
    <button
      className={cn(buttonVariants({ variant, size }), className)}
      {...props}
    />
  );
}
```

`className` goes through `cn()` last, so a caller can override any variant class.

## Accessible form input

```tsx
// components/ui/Input.tsx
import { cn } from '@/lib/cn';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: string;
}

export function Input({ className, error, id, ...props }: InputProps) {
  const errorId = id && error ? `${id}-error` : undefined;

  return (
    <div className="space-y-1">
      <input
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={errorId}
        className={cn(
          'w-full rounded-lg border bg-white px-3 py-2 text-sm',
          'transition-colors placeholder:text-gray-400',
          'focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-blue-500',
          'disabled:cursor-not-allowed disabled:opacity-50',
          'dark:bg-gray-900 dark:border-gray-700',
          error && 'border-red-500 focus-visible:ring-red-500',
          className
        )}
        {...props}
      />
      {error && (
        <p id={errorId} className="text-sm text-red-500">
          {error}
        </p>
      )}
    </div>
  );
}
```

The error text is linked with `aria-describedby`, so a screen reader reads it with the field.
