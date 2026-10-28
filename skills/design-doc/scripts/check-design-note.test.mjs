import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { MIN_SECTION_CHARS, REQUIRED, checkNote, parseNote } from './check-design-note.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const EM_DASH = String.fromCharCode(0x2014);

const SECTIONS = {
    problem: 'Clients cannot see which milestone a payment request belongs to, so they ask by message.',
    evidence: 'The portal list drops the milestone name: src/components/PaymentScheduleCard.tsx:42 (read at commit 5d82168). Issue #440.',
    'options considered': '1. **Show the milestone name in the card**: small change, no new data.\n2. **Add a separate milestone page**: more work, a new route.\n3. **Do nothing**: clients keep asking.',
    decision: 'Show the milestone name in the card, because it needs no new data and keeps one list.',
    invariants: '- A client reads only their own payment rows (the row-level policy stays unchanged).',
    'failure modes': '- A milestone with no name renders the schedule row title instead of an empty cell.',
    observability: 'The existing e2e on the payments list fails when the name is missing; no new log line.',
    rollback: 'Revert the one commit. No migration, no data change, so nothing to restore.',
};

function note({ spans = 'no', omit = [], override = {}, extra = '', level = '##' } = {}) {
    const sub = level + '#';
    const sections = { ...SECTIONS, ...override };
    if (spans === 'yes' && override.diagram === undefined) sections.diagram = '![Flow](payments/overview.png)\nSource: payments/overview.excalidraw';
    const body = Object.entries(sections).filter(([name]) => !omit.includes(name))
        .map(([name, text]) => `${sub} ${name[0].toUpperCase()}${name.slice(1)}\n${text}\n`).join('\n');
    return `# Plan\n\nintro\n\n${level} Design note: milestone name on the payment card\n\nStatus: proposed\nDate: 2026-10-21\nSpans components: ${spans}\n\n${body}\n${extra}`;
}

test('a complete note passes with no errors and no warnings', () => {
    const result = checkNote(note());
    assert.deepEqual(result.errors, []);
    assert.deepEqual(result.warnings, []);
});

test('a note that spans components passes only with a diagram section holding an image or a .excalidraw path', () => {
    assert.deepEqual(checkNote(note({ spans: 'yes' })).errors, []);
    assert.ok(checkNote(note({ spans: 'yes', omit: ['diagram'] }), {}).errors.some((error) => /section "diagram" is missing/.test(error)));
    const prose = checkNote(note({ spans: 'yes', override: { diagram: 'The flow goes from the portal to the admin through the queue.' } }));
    assert.ok(prose.errors.some((error) => /no image link and no \.excalidraw path/.test(error)));
});

test('every required section is demanded by name', () => {
    for (const name of REQUIRED) {
        const result = checkNote(note({ omit: [name] }));
        assert.ok(result.errors.some((error) => error.includes(`section "${name}" is missing`)), name);
    }
});

test('a section under the minimum length is an error', () => {
    const result = checkNote(note({ override: { rollback: 'Revert it.' } }));
    assert.ok(result.errors.some((error) => /section "rollback" is empty or under/.test(error)));
    assert.ok('Revert it.'.length < MIN_SECTION_CHARS);
});

test('one option is not a choice', () => {
    const result = checkNote(note({ override: { 'options considered': '1. **Only this**: we just do it, with no alternative weighed at all.' } }));
    assert.ok(result.errors.some((error) => /fewer than two options/.test(error)));
});

test('header lines are checked: status, real date, spans answer', () => {
    const base = note();
    assert.ok(checkNote(base.replace('Status: proposed\n', '')).errors.some((error) => /"Status:" line is missing/.test(error)));
    assert.ok(checkNote(base.replace('Status: proposed', 'Status: maybe')).errors.some((error) => /not proposed, accepted, superseded/.test(error)));
    assert.ok(checkNote(base.replace('Date: 2026-10-21\n', '')).errors.some((error) => /"Date:" line is missing/.test(error)));
    assert.ok(checkNote(base.replace('Date: 2026-10-21', 'Date: 2026-13-45')).errors.some((error) => /not a real YYYY-MM-DD date/.test(error)));
    assert.ok(checkNote(base.replace('Spans components: no\n', '')).errors.some((error) => /"Spans components: yes\|no" line is missing/.test(error)));
    assert.ok(checkNote(base.replace('Spans components: no', 'Spans components: maybe')).errors.some((error) => /must be yes or no/.test(error)));
});

test('a file with no Design note heading is an error', () => {
    const result = checkNote('# Plan\n\n## Notes\nnothing here\n');
    assert.equal(result.errors.length, 1);
    assert.match(result.errors[0], /no heading starting with "Design note"/);
});

test('the note ends at the next heading of its own level, so later sections of the plan are not read', () => {
    const text = note() + '\n## Next work\n\n### Rollback\nthis belongs to another section and must not rescue a missing one\n';
    assert.deepEqual(checkNote(text).errors, []);
    const missing = note({ omit: ['rollback'] }) + '\n## Next work\n\n### Rollback\nthis belongs to another section and must not rescue a missing one\n';
    assert.ok(checkNote(missing).errors.some((error) => /section "rollback" is missing/.test(error)));
});

test('a note works at any heading level and ignores headings inside code fences', () => {
    assert.deepEqual(checkNote(note({ level: '#' })).errors, []);
    const fenced = note({ extra: '```\n## Design note: a fake\n```\n' });
    assert.equal(parseNote(fenced).sections.size, Object.keys(SECTIONS).length);
});

test('warnings: a decision without a reason, evidence without a source, failure modes without a list', () => {
    assert.ok(checkNote(note({ override: { decision: 'Show the milestone name in the payment card as the answer.' } })).warnings.some((warning) => /never says why/.test(warning)));
    assert.ok(checkNote(note({ override: { evidence: 'The portal list drops the milestone name and clients ask by message about it.' } })).warnings.some((warning) => /cites no URL/.test(warning)));
    assert.ok(checkNote(note({ override: { 'failure modes': 'A milestone with no name renders the schedule row title instead of an empty cell.' } })).warnings.some((warning) => /no list items/.test(warning)));
});

test('evidence recognises a URL, a file:line, a commit hash and an issue number, and not a plain number', () => {
    for (const text of ['see https://example.com/regulation/section-4 read 2026-10-21', 'see src/admin/actions.ts:120 for the call', 'see commit b3e76c6e4 for the cut', 'tracked in #459 for later work']) {
        assert.deepEqual(checkNote(note({ override: { evidence: text } })).warnings, [], text);
    }
    assert.ok(checkNote(note({ override: { evidence: 'The amount is 1234567 shekels over a long time frame.' } })).warnings.some((warning) => /cites no URL/.test(warning)));
});

test('dashes, emoji and placeholders are errors; placeholders can be allowed for the template', () => {
    assert.ok(checkNote(note({ extra: `Done ${EM_DASH} ok\n` })).errors.some((error) => /em dash/.test(error)));
    assert.ok(checkNote(note({ extra: `Done ${String.fromCodePoint(0x1f680)}\n` })).errors.some((error) => /emoji/.test(error)));
    assert.ok(checkNote(note({ extra: 'TODO fill in\n' })).errors.some((error) => /placeholder/.test(error)));
    assert.deepEqual(checkNote(note({ extra: 'TODO fill in\n' }), { allowPlaceholders: true }).errors, []);
});

test('the shipped template has every required section and trips only the placeholder rule', () => {
    const template = readFileSync(join(here, '..', 'assets', 'design-note.md'), 'utf8')
        .replace('Date: {{YYYY-MM-DD}}', 'Date: 2026-10-21').replace('Spans components: {{yes or no}}', 'Spans components: yes')
        .replace(/\{\{Only when Spans[^\n]*\}\}/, '![Flow](payments/overview.png) payments/overview.excalidraw');
    assert.deepEqual(checkNote(template, { allowPlaceholders: true }).errors, []);
    assert.deepEqual(checkNote(template).errors.filter((error) => !/placeholder/.test(error)), []);
    assert.ok(checkNote(template).errors.some((error) => /placeholder/.test(error)));
});

test('the command line: exit codes and output', () => {
    const dir = mkdtempSync(join(tmpdir(), 'design-note-'));
    const good = join(dir, 'good.md');
    const bad = join(dir, 'bad.md');
    writeFileSync(good, note());
    writeFileSync(bad, note({ omit: ['rollback', 'invariants'] }));
    const run = (...args) => spawnSync(process.execPath, [join(here, 'check-design-note.mjs'), ...args], { encoding: 'utf8' });
    const ok = run(good);
    assert.equal(ok.status, 0, ok.stdout + ok.stderr);
    assert.match(ok.stdout, /0 errors/);
    const failed = run(bad);
    assert.equal(failed.status, 1);
    assert.match(failed.stdout, /ERROR section "rollback" is missing/);
    assert.match(failed.stdout, /ERROR section "invariants" is missing/);
    const missing = run(join(dir, 'none.md'));
    assert.equal(missing.status, 2);
    assert.match(missing.stderr, /does not exist/);
});
