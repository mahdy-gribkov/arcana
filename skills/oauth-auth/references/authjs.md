# Auth.js (NextAuth) with Google and token refresh

Loaded from SKILL.md. Use this when the app uses Auth.js with a JWT session and an OAuth provider that issues refresh tokens.

```typescript
import NextAuth from 'next-auth';
import GoogleProvider from 'next-auth/providers/google';
import { JWT } from 'next-auth/jwt';

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
      authorization: {
        params: {
          prompt: 'consent',
          access_type: 'offline',
          response_type: 'code'
        }
      }
    })
  ],
  session: {
    strategy: 'jwt',
    maxAge: 7 * 24 * 60 * 60 // 7 days
  },
  callbacks: {
    async jwt({ token, account, user }) {
      if (account && user) {
        return {
          ...token,
          accessToken: account.access_token,
          refreshToken: account.refresh_token,
          accessTokenExpires: account.expires_at! * 1000,
          userId: user.id
        };
      }

      // Return previous token if access token not expired
      if (Date.now() < (token.accessTokenExpires as number)) {
        return token;
      }

      // Refresh access token
      return await refreshAccessToken(token);
    },
    async session({ session, token }) {
      session.user.id = token.userId as string;
      session.accessToken = token.accessToken as string;
      return session;
    }
  }
});

async function refreshAccessToken(token: JWT) {
  try {
    const response = await fetch('https://oauth2.googleapis.com/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        client_id: process.env.GOOGLE_CLIENT_ID!,
        client_secret: process.env.GOOGLE_CLIENT_SECRET!,
        grant_type: 'refresh_token',
        refresh_token: token.refreshToken as string
      })
    });

    const refreshed = await response.json();

    if (!response.ok) {
      throw refreshed;
    }

    return {
      ...token,
      accessToken: refreshed.access_token,
      accessTokenExpires: Date.now() + refreshed.expires_in * 1000,
      refreshToken: refreshed.refresh_token ?? token.refreshToken
    };
  } catch (error) {
    return {
      ...token,
      error: 'RefreshAccessTokenError'
    };
  }
}
```
