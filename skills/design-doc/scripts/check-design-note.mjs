// Checks that a design note has the sections a non-trivial change needs before code starts.
//
// The note lives in a plan file or the README next to the code it describes, so it is a section of a larger file:
// the root is the heading whose text starts with "Design note". Its sub-headings (one level deeper) are the sections checked.
//     Status: proposed | accepted | superseded
//     Date: YYYY-MM-DD
//     Spans components: yes | no
//
// Usage: node check-design-note.mjs <file.md> [--allow-placeholders]
//   exit 0 = no errors, exit 1 = errors, exit 2 = unreadable input.
import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

export const STATUSES = ['proposed', 'accepted', 'superseded'];
export const REQUIRED = ['problem', 'evidence', 'options considered', 'decision', 'invariants', 'failure modes', 'observability', 'rollback'];
export const MIN_SECTION_CHARS = 20; // a one-word "none" is not an answer; say why nothing applies
const DASH = new RegExp(`[${String.fromCharCode(0x2013)}${String.fromCharCode(0x2014)}]`);
const PLACEHOLDER = /\{\{|\[TBD|\bTODO\b|\bFIXME\b/;
const EVIDENCE = /https?:\/\/\S+|\b[\w./-]+\.(?:ts|tsx|mjs|js|json|md|css|sql|yml|yaml|jsonc|toml):\d+|\b(?=[0-9a-f]*\d)(?=[0-9a-f]*[a-f])[0-9a-f]{7,40}\b|#\d+|`[^`]+\.(?:ts|tsx|mjs|md|css|sql|jsonc?)`/;
const DIAGRAM_REFERENCE = /!\[[^\]]*\]\([^)]+\)|\.excalidraw\b/;

/** Find the note root and cut its sections. Returns { found, level, preamble, sections: Map<name, text> }. */
export function parseNote(markdown) {
    const lines = markdown.split(/\r?\n/);
    let fenced = false;
    let rootIndex = -1;
    let level = 0;
    const headings = [];
    lines.forEach((line, index) => {
        if (/^\s*```/.test(line)) fenced = !fenced;
        const match = fenced ? null : /^(#{1,6})\s+(.+?)\s*$/.exec(line);
        if (match === null) return;
        headings.push({ index, level: match[1].length, text: match[2] });
        if (rootIndex < 0 && /^design note\b/i.test(match[2])) { rootIndex = headings.length - 1; level = match[1].length; }
    });
    if (rootIndex < 0) return { found: false, level: 0, preamble: '', sections: new Map() };
    const endHeading = headings.slice(rootIndex + 1).find((heading) => heading.level <= level);
    const end = endHeading === undefined ? lines.length : endHeading.index;
    const inside = headings.slice(rootIndex + 1).filter((heading) => heading.index < end && heading.level === level + 1);
    const sections = new Map();
    const firstSection = inside.length > 0 ? inside[0].index : end;
    const preamble = lines.slice(headings[rootIndex].index + 1, firstSection).join('\n');
    inside.forEach((heading, position) => {
        const next = inside[position + 1]?.index ?? end;
        sections.set(heading.text.toLowerCase().replace(/:$/, ''), lines.slice(heading.index + 1, next).join('\n'));
    });
    return { found: true, level, preamble, sections };
}

/** Errors and warnings for one note. */
export function checkNote(markdown, options = {}) {
    const errors = [];
    const warnings = [];
    const note = parseNote(markdown);
    if (!note.found) return { errors: ['no heading starting with "Design note" was found. Add "## Design note: <change>" to the plan or README.'], warnings };
    const { preamble, sections } = note;
    const status = /^Status:\s*(\S+)/im.exec(preamble)?.[1]?.toLowerCase();
    if (status === undefined) errors.push(`"Status:" line is missing under the Design note heading (${STATUSES.join(', ')}).`);
    else if (!STATUSES.includes(status)) errors.push(`Status "${status}" is not ${STATUSES.join(', ')}.`);
    const date = /^Date:\s*(\S+)/im.exec(preamble)?.[1];
    if (date === undefined) errors.push('"Date:" line is missing (YYYY-MM-DD, the day the decision was made).');
    else if (!/^\d{4}-\d{2}-\d{2}$/.test(date) || Number.isNaN(Date.parse(date))) errors.push(`Date "${date}" is not a real YYYY-MM-DD date.`);
    const spans = /^Spans components:\s*(\S+)/im.exec(preamble)?.[1]?.toLowerCase();
    if (spans === undefined) errors.push('"Spans components: yes|no" line is missing. A change across apps, packages or workers needs a diagram.');
    else if (!['yes', 'no'].includes(spans)) errors.push(`"Spans components:" must be yes or no, not "${spans}".`);

    const required = spans === 'yes' ? [...REQUIRED, 'diagram'] : REQUIRED;
    for (const name of required) {
        const text = sections.get(name);
        if (text === undefined) errors.push(`section "${name}" is missing (a heading ${'#'.repeat(note.level + 1)} ${name[0].toUpperCase()}${name.slice(1)}).`);
        else if (text.trim().length < MIN_SECTION_CHARS) errors.push(`section "${name}" is empty or under ${MIN_SECTION_CHARS} characters. Answer it, or say why it does not apply.`);
    }
    const options_ = sections.get('options considered') ?? '';
    const optionCount = (options_.match(/^\s*(?:#{1,6}\s+Option\b|\d+\.\s|[-*]\s+\*\*|[-*]\s+Option\b)/gim) ?? []).length;
    if (options_.trim() !== '' && optionCount < 2) errors.push('"Options considered" lists fewer than two options. Name the alternative you rejected, even if it is "do nothing".');
    const decision = sections.get('decision') ?? '';
    if (decision.trim() !== '' && !/\bbecause\b|\bwhy\b|\breason\b|\bso that\b/i.test(decision)) warnings.push('"Decision" never says why. State the reason next to the choice.');
    const evidence = sections.get('evidence') ?? '';
    if (evidence.trim() !== '' && !EVIDENCE.test(evidence)) warnings.push('"Evidence" cites no URL, file:line, commit or issue number. A claim without a source is unverified.');
    if (spans === 'yes' && (sections.get('diagram') ?? '').trim() !== '' && !DIAGRAM_REFERENCE.test(sections.get('diagram'))) {
        errors.push('"Diagram" holds no image link and no .excalidraw path. Build the diagram, or set "Spans components: no".');
    }
    const failure = sections.get('failure modes') ?? '';
    if (failure.trim() !== '' && (failure.match(/^\s*(?:[-*]|\d+\.)\s+\S/gm) ?? []).length < 1) warnings.push('"Failure modes" has no list items; one line per way it breaks and what happens then reads best.');
    if (DASH.test(markdown)) errors.push('the note has an en dash or an em dash; use a comma, a colon, parentheses or a plain hyphen.');
    if (/\p{Extended_Pictographic}/u.test(markdown)) errors.push('the note has an emoji; emojis are banned in every output.');
    if (options.allowPlaceholders !== true && PLACEHOLDER.test(markdown)) errors.push('the note still has a placeholder ({{...}}, [TBD], TODO or FIXME).');
    return { errors, warnings };
}

function main(argv) {
    const args = argv.slice(2);
    const file = args.find((arg) => !arg.startsWith('--'));
    if (file === undefined) { process.stderr.write('usage: node check-design-note.mjs <file.md> [--allow-placeholders]\n'); return 2; }
    if (!existsSync(file)) { process.stderr.write(`check-design-note: ${file} does not exist. Pass the plan or README that holds the note.\n`); return 2; }
    const result = checkNote(readFileSync(file, 'utf8'), { allowPlaceholders: args.includes('--allow-placeholders') });
    for (const error of result.errors) process.stdout.write(`ERROR ${error}\n`);
    for (const warning of result.warnings) process.stdout.write(`WARN  ${warning}\n`);
    process.stdout.write(`check-design-note: ${result.errors.length} errors, ${result.warnings.length} warnings\n`);
    return result.errors.length > 0 ? 1 : 0;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) process.exitCode = main(process.argv);
