import { test } from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync, spawnSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { scanPath, scanText } from './scan-package.mjs';

const SCRIPT = join(dirname(fileURLToPath(import.meta.url)), 'scan-package.mjs');
const rules = (text) => scanText(text).map((finding) => finding.rule);
// Windows profile paths are built from parts so no literal user path sits in this file.
const windowsPath = (...parts) => ['C:', 'Users', ...parts].join('\\');

test('clean text with reserved domains and placeholders has no findings', () => {
    const text = [
        'fetch("http://localhost:3000/x")',
        'fetch("https://attacker.example.com/cb")',
        'contact: researcher@example.com',
        `path: ${windowsPath('<name>', 'poc')}`,
        'path: /home/user/poc/',
        'a plain hyphen - is fine',
    ].join('\n');
    assert.deepEqual(scanText(text), []);
});

test('flags a real email, a production endpoint and local user paths', () => {
    assert.deepEqual(rules('mail me at jane.doe@gmail.com'), ['email']);
    assert.deepEqual(rules('curl https://api.vendor-prod.com/v1/items'), ['external-endpoint']);
    assert.deepEqual(rules(`open ${windowsPath('jane', 'Desktop', 'poc.js')}`), ['windows-user-path']);
    assert.deepEqual(rules('cd /Users/jane/work/poc/'), ['unix-home-path']);
    assert.deepEqual(rules('cd /home/jane/work/'), ['unix-home-path']);
});

test('flags secrets and never prints their value', () => {
    const token = `ghp_${'a1B2c3D4e5'.repeat(4)}`;
    const found = scanText(`const t = "${token}"`);
    assert.equal(found[0].rule, 'secret-github-token');
    assert.equal(found[0].excerpt, '[redacted]');
    assert.ok(!JSON.stringify(found).includes(token));
    assert.deepEqual(rules('AKIAABCDEFGHIJKLMNOP'), ['secret-aws-key']);
    assert.deepEqual(rules('-----BEGIN RSA PRIVATE KEY-----'), ['secret-private-key']);
    assert.deepEqual(rules('password = "hunter2hunter2hunter2"'), ['secret-assignment']);
    assert.deepEqual(rules('const jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abc123"'), ['secret-jwt']);
});

test('flags em dash, en dash and emoji', () => {
    assert.deepEqual(rules(`a ${String.fromCharCode(0x2014)} b`), ['dash-character']);
    assert.deepEqual(rules(`1${String.fromCharCode(0x2013)}2`), ['dash-character']);
    assert.deepEqual(rules('done \u{1F680}'), ['emoji']);
});

test('reports 1-based line numbers', () => {
    const [finding] = scanText('ok\nok\nsee jane@gmail.com');
    assert.equal(finding.line, 3);
});

test('scanPath walks a folder, skips node_modules and binaries, reports relative paths', () => {
    const dir = mkdtempSync(join(tmpdir(), 'poc-'));
    mkdirSync(join(dir, 'node_modules', 'pkg'), { recursive: true });
    writeFileSync(join(dir, 'node_modules', 'pkg', 'index.js'), 'jane@gmail.com');
    writeFileSync(join(dir, 'poc.js'), 'ok');
    writeFileSync(join(dir, 'README.md'), 'contact jane@gmail.com');
    writeFileSync(join(dir, 'shot.png'), Buffer.from([0, 1, 2, 0x6a, 0x61, 0x6e, 0x65, 0x40]));
    const results = scanPath(dir);
    assert.deepEqual(results.map((result) => [result.file, result.rule]), [['README.md', 'email']]);
});

test('scanPath refuses an archive and a missing path with actionable errors', () => {
    assert.throws(() => scanPath('poc.zip'), /extract it into an empty folder/);
    assert.throws(() => scanPath(join(tmpdir(), 'no-such-folder-for-scan')), /does not exist/);
});

test('the CLI exits 0 on a clean folder, 1 on findings, 2 on bad usage', () => {
    const clean = mkdtempSync(join(tmpdir(), 'poc-'));
    writeFileSync(join(clean, 'a.txt'), 'nothing here');
    assert.match(execFileSync('node', [SCRIPT, clean], { encoding: 'utf8' }), /0 finding/);
    const dirty = mkdtempSync(join(tmpdir(), 'poc-'));
    writeFileSync(join(dirty, 'a.txt'), 'jane@gmail.com');
    const failed = spawnSync('node', [SCRIPT, dirty], { encoding: 'utf8' });
    assert.equal(failed.status, 1);
    assert.match(failed.stdout, /a\.txt:1 email/);
    assert.equal(spawnSync('node', [SCRIPT], { encoding: 'utf8' }).status, 2);
    const asJson = spawnSync('node', [SCRIPT, dirty, '--json'], { encoding: 'utf8' });
    assert.equal(JSON.parse(asJson.stdout)[0].rule, 'email');
});
