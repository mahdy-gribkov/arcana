// Scan a PoC package folder for what must not ship in a bug bounty submission: personal data, secrets,
// local user paths, production endpoints, dashes and emojis. Exit 1 when anything is found.
// Usage: node scan-package.mjs <folder-or-file> [--json]
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { extname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const SKIP_DIRECTORIES = new Set(['node_modules', '.git']);
const BINARY_EXTENSIONS = new Set(['.png', '.jpg', '.jpeg', '.gif', '.webp', '.pdf', '.zip', '.gz', '.tar', '.7z', '.ico', '.woff', '.woff2', '.ttf', '.mp4', '.mov']);
const RESERVED_HOST = /^(?:localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\]|(?:[\w-]+\.)*(?:example\.(?:com|org|net)|test|invalid|example|localhost))(?::\d+)?$/i;
const RESERVED_EMAIL_DOMAIN = /@(?:[\w-]+\.)*(?:example\.(?:com|org|net)|test|invalid|example)$/i;
const MAX_EXCERPT = 100;

/** Rules whose matched value is a secret: the report prints the rule and place, never the value. */
const RULES = [
    { id: 'secret-aws-key', secret: true, pattern: /\bAKIA[0-9A-Z]{16}\b/ },
    { id: 'secret-github-token', secret: true, pattern: /\bgh[pousr]_[A-Za-z0-9]{36,}\b/ },
    { id: 'secret-api-key', secret: true, pattern: /\bsk-[A-Za-z0-9_-]{20,}\b/ },
    { id: 'secret-slack-token', secret: true, pattern: /\bxox[baprs]-[A-Za-z0-9-]{10,}\b/ },
    { id: 'secret-private-key', secret: true, pattern: /-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----/ },
    { id: 'secret-jwt', secret: true, pattern: /\beyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]+/ },
    { id: 'secret-assignment', secret: true, pattern: /\b(?:api[_-]?key|secret|token|password|passwd)\b\s*[:=]\s*['"][^'"\s]{12,}['"]/i },
    { id: 'windows-user-path', pattern: /\b[A-Za-z]:\\+Users\\+(?!<|\{|%|Public\b|Default\b)[^\\\s<>"']+/ },
    { id: 'unix-home-path', pattern: /(?:\/Users|\/home)\/(?!<|\{|\$|user\b|username\b|runner\b)[A-Za-z0-9._-]+\// },
    // Built from code points: the no-dash rule applies to this source too, including as an escape.
    { id: 'dash-character', pattern: new RegExp(`[${String.fromCharCode(0x2013)}${String.fromCharCode(0x2014)}]`) },
    { id: 'emoji', pattern: /[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}\u{1F000}-\u{1F2FF}]/u },
];
const EMAIL = /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/g;
const URL_PATTERN = /\bhttps?:\/\/([^\s/"'`<>)\]]+)/gi;

function excerpt(line) {
    const trimmed = line.trim();
    return trimmed.length > MAX_EXCERPT ? `${trimmed.slice(0, MAX_EXCERPT)}...` : trimmed;
}

/** Findings for one file's text: [{ line, rule, excerpt }]. */
export function scanText(text) {
    const findings = [];
    text.split(/\r?\n/).forEach((line, index) => {
        const lineNumber = index + 1;
        for (const rule of RULES) {
            if (rule.pattern.test(line)) findings.push({ line: lineNumber, rule: rule.id, excerpt: rule.secret ? '[redacted]' : excerpt(line) });
        }
        for (const [email] of line.matchAll(EMAIL)) {
            if (!RESERVED_EMAIL_DOMAIN.test(email)) findings.push({ line: lineNumber, rule: 'email', excerpt: excerpt(line) });
        }
        for (const [, host] of line.matchAll(URL_PATTERN)) {
            const bareHost = host.includes('@') ? host.split('@').pop() : host;
            if (!RESERVED_HOST.test(bareHost)) findings.push({ line: lineNumber, rule: 'external-endpoint', excerpt: excerpt(line) });
        }
    });
    return findings;
}

function collectFiles(target) {
    if (!statSync(target).isDirectory()) return [target];
    const files = [];
    for (const entry of readdirSync(target, { withFileTypes: true })) {
        if (entry.isDirectory() && SKIP_DIRECTORIES.has(entry.name)) continue;
        const path = join(target, entry.name);
        if (entry.isDirectory()) files.push(...collectFiles(path));
        else files.push(path);
    }
    return files;
}

/** Scan a folder or a single file. Throws an actionable Error for a zip or a missing path. */
export function scanPath(target) {
    const absolute = resolve(target);
    if (/\.(zip|tgz|gz|tar|7z)$/i.test(absolute)) {
        throw new Error(`Cannot scan the archive ${absolute}: extract it into an empty folder and scan that folder, so every packaged file is read.`);
    }
    let stats;
    try {
        stats = statSync(absolute);
    } catch {
        throw new Error(`Cannot scan ${absolute}: the path does not exist. Pass the PoC package folder.`);
    }
    const root = stats.isDirectory() ? absolute : resolve(absolute, '..');
    const results = [];
    for (const file of collectFiles(absolute)) {
        if (BINARY_EXTENSIONS.has(extname(file).toLowerCase())) continue;
        const buffer = readFileSync(file);
        if (buffer.includes(0)) continue;
        for (const finding of scanText(buffer.toString('utf8'))) results.push({ file: relative(root, file).split('\\').join('/'), ...finding });
    }
    return results;
}

function main() {
    const args = process.argv.slice(2);
    const asJson = args.includes('--json');
    const target = args.find((arg) => !arg.startsWith('--'));
    if (!target) {
        process.stderr.write('Usage: node scan-package.mjs <package-folder> [--json]\n');
        process.exitCode = 2;
        return;
    }
    let results;
    try {
        results = scanPath(target);
    } catch (error) {
        process.stderr.write(`${error.message}\n`);
        process.exitCode = 2;
        return;
    }
    if (asJson) process.stdout.write(`${JSON.stringify(results, null, 2)}\n`);
    else {
        for (const result of results) process.stdout.write(`${result.file}:${result.line} ${result.rule} ${result.excerpt}\n`);
        process.stdout.write(`scan-package: ${results.length} finding(s)\n`);
    }
    process.exitCode = results.length === 0 ? 0 : 1;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
