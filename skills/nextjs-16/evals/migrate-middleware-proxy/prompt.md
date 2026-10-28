---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---
We upgraded the app to Next.js 16. Migrate this file to the new convention.

```ts
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  if (!request.cookies.get('session')) {
    return NextResponse.redirect(new URL('/login', request.url));
  }
  return NextResponse.next();
}

export const config = { matcher: ['/account/:path*'] };
```
