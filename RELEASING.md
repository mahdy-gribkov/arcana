# Release Protocol

## Before Bumping a Version

Run the full gate set from `cli/`. It is the same set CI runs:

```bash
pnpm install --frozen-lockfile
pnpm run ci
```

`pnpm run ci` runs lint, the format check, the type check, the tests with coverage and the build. It then runs
`scripts/check-skills.sh` (validate, cross-validate, quality floor, skill script tests) and `scripts/security-scan.sh`.

Also check by hand:
1. CHANGELOG.md has an entry for the new version.
2. README.md skill count and badges match `skills/`.
3. CITATION.cff version and date are updated.

## Version Types

- **patch** (5.0.x): bug fixes, skill content updates, typo fixes
- **minor** (5.x.0): new skills, new commands, new features
- **major** (x.0.0): breaking changes (removed or renamed skills, removed commands, API changes)

## Release Steps

1. Bump `cli/package.json` `version`, `.claude-plugin/marketplace.json` `metadata.version` and every entry `version`
   to the same value. `src/release.test.ts` and `validate --cross` fail when they differ; Claude Code uses the entry
   version as its update signal.
2. Update `CHANGELOG.md` and `CITATION.cff`.
3. `pnpm run ci` in `cli/`.
4. Commit: `chore: release vX.Y.Z`.
5. Push to `master` and wait for every CI job to pass.
6. Tag `vX.Y.Z` and push the tag. `.github/workflows/publish.yml` builds, tests and publishes with provenance.

## Never Publish Locally

Every npm publish goes through GitHub Actions for provenance attestation. A local `npm publish` skips provenance and
the CI gates.

## After Release

1. `npm view @sporesec/arcana version`
2. Check the provenance badge on npmjs.com.
