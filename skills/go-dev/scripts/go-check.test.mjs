import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { after, describe, it } from 'node:test';
import { fileURLToPath } from 'node:url';
import { BASELINE_CONFIG, buildPlan, findCiPin, findRepoConfig, parseLintVersion, runGoCheck } from './go-check.mjs';

const SCRIPT = join(dirname(fileURLToPath(import.meta.url)), 'go-check.mjs');
const made = [];

function makeModule(files) {
    const directory = mkdtempSync(join(tmpdir(), 'go-check-'));
    made.push(directory);
    for (const [name, content] of Object.entries(files)) {
        mkdirSync(dirname(join(directory, name)), { recursive: true });
        writeFileSync(join(directory, name), content);
    }
    return directory;
}

after(() => { for (const directory of made) rmSync(directory, { recursive: true, force: true }); });

const GO_MOD = 'module example.com/fixture\n\ngo 1.22\n';
const CLEAN_MAIN = 'package main\n\nfunc main() {}\n';
const VET_ERROR_MAIN = 'package main\n\nimport "fmt"\n\nfunc main() {\n\tfmt.Printf("%d\\n", "not a number")\n}\n';

/** A fake process runner: `answers` maps "tool arg0 arg1" prefixes to a result; everything else succeeds with no output. */
function fakeRunner(answers = {}) {
    const calls = [];
    const run = (command, args) => {
        const key = [command, ...args].join(' ');
        calls.push(key);
        const hit = Object.entries(answers).find(([prefix]) => key.startsWith(prefix));
        const base = { status: 0, stdout: '', stderr: '', error: null };
        return hit === undefined ? base : { ...base, ...hit[1] };
    };
    return { run, calls };
}

const noMissingLint = { 'go env': { stdout: '1\n' }, 'golangci-lint version': { stdout: 'golangci-lint has version 2.15.0 built with go1.26.1\n' } };

describe('inputs', () => {
    it('exits 2 with an actionable message when the directory has no go.mod', () => {
        const directory = makeModule({ 'README.md': 'not a go module\n' });
        const result = runGoCheck({ directory, fast: true, run: fakeRunner().run });
        assert.equal(result.exitCode, 2);
        assert.match(result.lines[0], /no go\.mod in .*Run it from a Go module root/);
    });

    it('the CLI prints that message on stderr and exits 2', () => {
        const directory = makeModule({ 'README.md': 'x\n' });
        const result = spawnSync(process.execPath, [SCRIPT, directory], { encoding: 'utf8' });
        assert.equal(result.status, 2);
        assert.match(result.stderr, /no go\.mod in/);
        assert.equal(result.stdout, '');
    });

    it('reads the golangci-lint version and the CI pin', () => {
        assert.equal(parseLintVersion('golangci-lint has version 2.15.0 built with go1.26.1'), '2.15.0');
        assert.equal(parseLintVersion('golangci-lint has version v2.12.2 built'), '2.12.2');
        assert.equal(parseLintVersion('command not found'), null);
        const directory = makeModule({
            'go.mod': GO_MOD,
            '.github/workflows/lint.yml': 'jobs:\n  lint:\n    steps:\n      - uses: golangci/golangci-lint-action@v7\n        with:\n          version: v2.12.2\n',
            '.github/workflows/other.yml': 'jobs:\n  x:\n    steps:\n      - uses: actions/setup-node@v4\n        with:\n          version: v9.9.9\n',
        });
        assert.equal(findCiPin(directory), '2.12.2');
        assert.equal(findCiPin(makeModule({ 'go.mod': GO_MOD })), null);
    });
});

describe('lint config choice', () => {
    it('uses the repo own config and passes no --config flag', () => {
        const directory = makeModule({ 'go.mod': GO_MOD, '.golangci.yml': 'version: "2"\n' });
        assert.equal(findRepoConfig(directory), '.golangci.yml');
        const { run, calls } = fakeRunner(noMissingLint);
        const { lines } = runGoCheck({ directory, fast: true, run });
        assert.ok(lines.some((line) => line.includes("INFO  lint config: the repo's own .golangci.yml")));
        assert.equal(calls.filter((call) => call.includes('--config')).length, 0);
    });

    it('falls back to the bundled baseline, which exists, and says so', () => {
        const directory = makeModule({ 'go.mod': GO_MOD });
        assert.ok(existsSync(BASELINE_CONFIG), 'assets/golangci.yml must ship with the skill');
        const { run, calls } = fakeRunner(noMissingLint);
        const { lines } = runGoCheck({ directory, fast: true, run });
        assert.ok(lines.some((line) => line.includes('none in the repo, using the bundled baseline')));
        assert.equal(calls.filter((call) => call.startsWith('golangci-lint run') && call.includes(`--config ${BASELINE_CONFIG}`)).length, 1);
    });
});

describe('gate lines', () => {
    it('warns about version drift against the CI pin without failing', () => {
        const directory = makeModule({ 'go.mod': GO_MOD, '.github/workflows/lint.yml': 'name: golangci-lint\nversion: v2.12.2\n' });
        const { lines, exitCode } = runGoCheck({ directory, fast: true, run: fakeRunner(noMissingLint).run });
        assert.ok(lines.some((line) => line.startsWith('  WARN  golangci-lint 2.15.0 locally, CI pins 2.12.2')));
        assert.equal(exitCode, 0);
    });

    it('reports a missing tool as MISS with an install hint and exits 1', () => {
        const directory = makeModule({ 'go.mod': GO_MOD });
        const missing = { code: 'ENOENT' };
        const { run } = fakeRunner({ 'go env': { stdout: '1\n' }, 'golangci-lint': { error: missing }, govulncheck: { error: missing } });
        const { lines, exitCode } = runGoCheck({ directory, fast: false, run });
        assert.equal(exitCode, 1);
        assert.ok(lines.some((line) => /^ {2}MISS {2}golangci-lint run: golangci-lint is not installed \(install the pinned binary/.test(line)));
        assert.ok(lines.some((line) => /^ {2}MISS {2}govulncheck .*go install golang\.org\/x\/vuln\/cmd\/govulncheck@latest/.test(line)));
        assert.ok(lines.some((line) => line === '  PASS  go vet'));
    });

    it('fails the format gate when the diff is not empty even though the exit code is 0', () => {
        const directory = makeModule({ 'go.mod': GO_MOD });
        const { run } = fakeRunner({ ...noMissingLint, 'golangci-lint fmt': { stdout: '--- a/main.go\n+++ b/main.go\n@@ -1 +1 @@\n' } });
        const { lines, exitCode } = runGoCheck({ directory, fast: true, run });
        assert.equal(exitCode, 1);
        const failAt = lines.findIndex((line) => line.startsWith('  FAIL  format:'));
        assert.ok(failAt >= 0);
        assert.match(lines[failAt + 1], /^ {8}--- a\/main\.go$/);
    });

    it('caps the printed output of a failing gate', () => {
        const directory = makeModule({ 'go.mod': GO_MOD });
        const noisy = Array.from({ length: 60 }, (_, index) => `problem ${index}`).join('\n');
        const { run } = fakeRunner({ ...noMissingLint, 'go vet': { status: 1, stderr: noisy } });
        const { lines } = runGoCheck({ directory, fast: true, run });
        const failAt = lines.findIndex((line) => line === '  FAIL  go vet');
        const printed = lines.slice(failAt + 1).filter((line) => line.startsWith('        problem'));
        assert.equal(printed.length, 20);
    });

    it('--fast skips govulncheck and the test run and says so', () => {
        const directory = makeModule({ 'go.mod': GO_MOD });
        const { run, calls } = fakeRunner(noMissingLint);
        const { lines, exitCode } = runGoCheck({ directory, fast: true, run });
        assert.equal(exitCode, 0);
        assert.ok(lines.includes('  skip  govulncheck and go test (--fast)'));
        assert.equal(calls.filter((call) => call.startsWith('govulncheck') || call.startsWith('go test')).length, 0);
        assert.equal(lines.at(-1), 'go-check: ALL PASS');
    });

    it('runs go test -race when cgo is on, and without -race (with a warning) when it is off', () => {
        const directory = makeModule({ 'go.mod': GO_MOD });
        const withCgo = fakeRunner(noMissingLint);
        runGoCheck({ directory, fast: false, run: withCgo.run });
        assert.ok(withCgo.calls.includes('go test -race -count=1 ./...'));
        const withoutCgo = fakeRunner({ ...noMissingLint, 'go env': { stdout: '0\n' } });
        const { lines } = runGoCheck({ directory, fast: false, run: withoutCgo.run });
        assert.ok(withoutCgo.calls.includes('go test -count=1 ./...'));
        assert.ok(lines.some((line) => line.includes('the race detector needs cgo')));
    });

    it('builds the plan in CI order', () => {
        const labels = buildPlan({ fast: false, raceAvailable: true, configArgs: [] }).map((step) => step.tool + ' ' + step.args[0]);
        assert.deepEqual(labels, ['golangci-lint fmt', 'golangci-lint run', 'go vet', 'go mod', 'govulncheck ./...', 'go test']);
    });
});

const goInstalled = spawnSync('go', ['version'], { encoding: 'utf8' }).error === undefined;

describe('against a real Go toolchain', { skip: goInstalled ? false : 'go is not installed' }, () => {
    it('fails go vet on a printf verb mismatch and passes go vet on clean code', () => {
        const broken = makeModule({ 'go.mod': GO_MOD, 'main.go': VET_ERROR_MAIN });
        const bad = runGoCheck({ directory: broken, fast: true });
        assert.ok(bad.lines.includes('  FAIL  go vet'), bad.lines.join('\n'));
        assert.ok(bad.lines.some((line) => /Printf format %d has arg .* of wrong type string/.test(line)));
        assert.equal(bad.exitCode, 1);

        const clean = makeModule({ 'go.mod': GO_MOD, 'main.go': CLEAN_MAIN });
        const good = runGoCheck({ directory: clean, fast: true });
        assert.ok(good.lines.includes('  PASS  go vet'), good.lines.join('\n'));
        assert.ok(good.lines.includes('  PASS  go mod tidy leaves no diff'), good.lines.join('\n'));
    });

    it('fails the tidy gate when go.mod requires a module no code imports', () => {
        // The unused requirement points at a local replace target, so tidy needs no network.
        const untidy = makeModule({
            'go.mod': `${GO_MOD}\nrequire example.com/unused v1.0.0\n\nreplace example.com/unused => ./unused\n`,
            'unused/go.mod': 'module example.com/unused\n\ngo 1.22\n',
            'main.go': CLEAN_MAIN,
        });
        const { lines } = runGoCheck({ directory: untidy, fast: true });
        assert.ok(lines.includes('  FAIL  go mod tidy leaves no diff'), lines.join('\n'));
    });

    it('runs go test for real and fails on a failing test', () => {
        const failing = makeModule({
            'go.mod': GO_MOD,
            'main.go': CLEAN_MAIN,
            'main_test.go': 'package main\n\nimport "testing"\n\nfunc TestBroken(t *testing.T) {\n\tt.Fatal("boom")\n}\n',
        });
        const { lines } = runGoCheck({ directory: failing, fast: false });
        const testLine = lines.find((line) => /^ {2}FAIL {2}go test/.test(line));
        assert.ok(testLine !== undefined, lines.join('\n'));
        assert.ok(lines.some((line) => line.includes('TestBroken')));
    });
});
