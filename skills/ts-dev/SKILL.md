---
name: ts-dev
description: Writes and reviews TypeScript, React and Next.js code against one senior checklist (outcome, what becomes dead, reuse, names, types parsed once, one error model, boundaries, required config values, comments) and one findings format. Use when reviewing a TypeScript or TSX diff or a PR, asked "is this idiomatic TypeScript" or "review my code", designing a type, an error shape or a function signature, replacing any, a non-null assertion or a type cast, fixing a tsc or typescript-eslint complaint, or deciding whether to extract a helper or add a layer. Not for building a page, route or migration (nextjs-16, api-design, database-design), writing tests (testing), Go (go-dev) or design notes (design-doc).
allowed-tools: Read, Glob, Grep, Bash(npx tsc:*), Bash(npx eslint:*), Bash(npx knip:*), Bash(pnpm run:*), Bash(npm run:*)
---

# TypeScript development and review

Scope: anything in `.ts`, `.tsx`, `.mts` or `.cts` files. This skill adds a review method and the code shapes on top of a short baseline
of conventions. If the project already has written conventions, a tsconfig and a lint config, those win over the baseline below; prose
here covers only what a tool cannot decide.

## Baseline conventions

- Strict compiler settings and typescript-eslint `strictTypeChecked` plus `stylisticTypeChecked` (details in `references/typescript-strict.md`).
- Names say what a thing is or does, in domain words. Not the vendor (`sendBrevoEmail`), not an empty label (Manager, Helper, Util,
  Service, Data, Info). One concept, one name across code, database, screens and docs.
- Reuse before writing: look in the shared modules and read the two nearest siblings first. A second copy of logic is extracted into one
  home and the copies are deleted; a third copy is a defect.
- A value a caller can forget (env, config, id, limit, timeout, locale, tenant) is required, with no default.
- Errors say what failed, why and what to try. No empty `catch`. No secret or personal data in a log or a message.
- Comments explain a reason the code cannot show, and are kept true in the same commit as the code they describe.

## Workflow

1. **Know the target.** Read the touched package's README, `tsconfig` and the lint config. Grep the shared modules and read the two
   nearest siblings of the code under review.
2. **Run the mechanical gates before judging anything.** The project's type-check and lint scripts (or `npx tsc --noEmit` and
   `npx eslint .`), plus any dead-code check such as knip. Report one line per gate: PASS, FAIL, or MISS (not run, with the reason).
   Everything a tool reports is settled by the tool; never restate it as a finding. Do not call a change clean on a partial run.
3. **Review the judgment items** in `references/review-checklist.md`.
4. **Write the findings** in the format of `references/review-output.md` (file:line, why, fix with an effort estimate, source).
5. **Writing new code?** Pick the reference from the table, write it, then run the gates again.

## Which reference

| Task | Read |
| --- | --- |
| Review judgment: outcome, deletion, reuse, layers, types, errors, names, boundaries, comments | `references/review-checklist.md` |
| Writing up review findings | `references/review-output.md` |
| Error values and throws, boundary parsing, options objects, derived types, async shapes | `references/idioms.md` |
| Replacing `any`, `!`, `as`; unions and exhaustiveness; brands; generics; constants; regex; compiler and lint baseline | `references/typescript-strict.md` |

## Rules that bite

- Fix the code, never the check. An escape is `eslint-disable-next-line <rule> -- <reason>`; a disable without a rule name and a reason is
  a finding. A check that only repeats the compiler is wrong and is removed with proof, not bent around.
- A value a caller can forget (env, config, id, limit, timeout, locale, tenant) has no default. It is required, and a missing value fails at
  the boundary.
- A problem found outside the change under review is still a finding: put it in the plan or an issue that names the layer which fixes it.
- Verify a version-gated language or library feature against the installed version and its release notes before recommending it.

Related skills: `testing` for tests, `go-dev` for Go, `design-doc` for a design note, `security-review` for a security pass,
`nextjs-16` for building pages and routes.

## Evidence

Cite file:line for every claim about the code. Quote the failing gate line for every claim that a gate fails. Name the gates that did not
run. Do not call a change safe to merge on a partial run.
