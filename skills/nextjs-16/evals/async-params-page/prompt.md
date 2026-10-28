---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---
This page worked on Next.js 14 and breaks after upgrading to 16 with a params error. Fix it.

```tsx
// app/blog/[slug]/page.tsx
export default async function Post({ params }: { params: { slug: string } }) {
  const post = await db.posts.findUnique({ where: { slug: params.slug } });
  return <article><h1>{post.title}</h1></article>;
}

export async function generateMetadata({ params }: { params: { slug: string } }) {
  return { title: params.slug };
}
```
