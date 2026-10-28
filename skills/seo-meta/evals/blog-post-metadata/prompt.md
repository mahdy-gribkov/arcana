---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---
Add proper SEO metadata to this Next.js 16 blog post page: title, description, canonical URL, Open Graph and Twitter cards.

```tsx
// app/blog/[slug]/page.tsx
export default async function Post({ params }) {
  const { slug } = await params;
  const post = await getPost(slug);
  return <article><h1>{post.title}</h1></article>;
}
```
