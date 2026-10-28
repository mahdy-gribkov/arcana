// go-check.mjs: the mechanical Go gates in one place, one PASS/FAIL/MISS line each, so a review spends its time on judgment.
//
// Usage: node scripts/go-check.mjs [module-dir] [--fast]
//   --fast skips govulncheck and the race run (the slow steps).
// Exit codes: 0 every gate passed, 1 a gate failed or a tool is missing, 2 bad input (no go.mod).
//
// The lint config is the repo's own .golangci.* file when it has one; otherwise the bundled baseline in
// ../assets/golangci.yml, and the report says so (a repo with no lint config is itself the first review finding).
import { spawnSync } from 'node:child_process';
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
export const BASELINE_CONFIG = join(HERE, '..', 'assets', 'golangci.yml');
export const LINES_PER_FAILURE = 20;
// Reference version, read from the upstream release page when this script was written. A repo's CI pin always wins over it.
export const REFERENCE_GOLANGCI_LINT = 'v2.15.0';
export const GOLANGCI_INSTALL_DOC = 'https://golangci-lint.run/docs/welcome/install/local/';
export const GOVULNCHECK_INSTALL = 'go install golang.org/x/vuln/cmd/govulncheck@latest';
const CONFIG_NAMES = ['.golangci.yml', '.golangci.yaml', '.golangci.toml', '.golangci.json'];

/** The repo's own golangci-lint config file name, or null when it has none. */
export function findRepoConfig(directory) {
    return CONFIG_NAMES.find((name) => existsSync(join(directory, name))) ?? null;
}

/** The golangci-lint version a repo's CI workflows pin (for example "2.12.2"), or null. */
export function findCiPin(directory) {
    const workflows = join(directory, '.github', 'workflows');
    if (!existsSync(workflows)) return null;
    for (const file of readdirSync(workflows).filter((name) => /\.ya?ml$/.test(name))) {
        const text = readFileSync(join(workflows, file), 'utf8');
        if (!/golangci-lint/.test(text)) continue;
        const match = /version:\s*["']?v?(2\.\d+\.\d+)/.exec(text);
        if (match !== null) return match[1];
    }
    return null;
}

/** The version number in `golangci-lint version` output, or null. */
export function parseLintVersion(output) {
    const match = /version\s+v?(\d+\.\d+\.\d+)/.exec(output);
    return match === null ? null : match[1];
}

/** The ordered gate list. `configArgs` is [] for a repo with its own config, else ["--config", baseline]. */
export function buildPlan({ fast, raceAvailable, configArgs }) {
    const plan = [
        { label: 'format: gofumpt + goimports (golangci-lint fmt --diff)', tool: 'golangci-lint', args: ['fmt', '--diff', ...configArgs, './...'], cleanOutput: true },
        { label: 'golangci-lint run', tool: 'golangci-lint', args: ['run', ...configArgs, './...'] },
        { label: 'go vet', tool: 'go', args: ['vet', './...'] },
        { label: 'go mod tidy leaves no diff', tool: 'go', args: ['mod', 'tidy', '-diff'] },
    ];
    if (!fast) plan.push({ label: 'govulncheck (dependencies and stdlib, call-graph aware)', tool: 'govulncheck', args: ['./...'] });
    if (!fast) {
        plan.push(raceAvailable
            ? { label: 'go test -race -count=1', tool: 'go', args: ['test', '-race', '-count=1', './...'] }
            : { label: 'go test -count=1 (no race detector: needs cgo)', tool: 'go', args: ['test', '-count=1', './...'] });
    }
    return plan;
}

const INSTALL_HINTS = {
    'golangci-lint': `install the pinned binary (${GOLANGCI_INSTALL_DOC}; ${REFERENCE_GOLANGCI_LINT} is the reference, but use the version your CI pins)`,
    govulncheck: GOVULNCHECK_INSTALL,
    go: 'install Go from https://go.dev/dl/',
};

/** Default process runner: no shell, so a module path with spaces or metacharacters is one argument. */
export function spawnRunner(command, args, cwd) {
    const result = spawnSync(command, args, { cwd, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 });
    return { status: result.status, stdout: result.stdout ?? '', stderr: result.stderr ?? '', error: result.error ?? null };
}

function indent(text) {
    return text.split(/\r?\n/).filter((line) => line.length > 0).slice(0, LINES_PER_FAILURE).map((line) => `        ${line}`);
}

/** Runs every gate in `directory` and returns { exitCode, lines }. `run` is injectable so tests need no toolchain. */
export function runGoCheck({ directory, fast = false, run = spawnRunner }) {
    const root = resolve(directory);
    if (!existsSync(join(root, 'go.mod'))) {
        return { exitCode: 2, lines: [`go-check: no go.mod in ${root}. Run it from a Go module root or pass the module directory as the first argument.`] };
    }
    const lines = [`== go-check: ${root} ==`];
    const repoConfig = findRepoConfig(root);
    const configArgs = repoConfig === null ? ['--config', BASELINE_CONFIG] : [];
    lines.push(repoConfig === null
        ? '  INFO  lint config: none in the repo, using the bundled baseline (finding: adopt assets/golangci.yml and set the goimports local-prefixes)'
        : `  INFO  lint config: the repo's own ${repoConfig}`);

    const lintVersion = run('golangci-lint', ['version'], root);
    const installed = lintVersion.error === null ? parseLintVersion(`${lintVersion.stdout}${lintVersion.stderr}`) : null;
    const pin = findCiPin(root);
    if (installed !== null && pin !== null) {
        lines.push(installed === pin
            ? `  PASS  golangci-lint ${installed} matches the CI pin`
            : `  WARN  golangci-lint ${installed} locally, CI pins ${pin} (results can differ; install ${pin}, do not relax the config)`);
    } else if (pin === null) {
        lines.push('  INFO  no golangci-lint pin in .github/workflows (CI does not lint this repo, or does not pin a version)');
    }

    const cgo = run('go', ['env', 'CGO_ENABLED'], root);
    const raceAvailable = cgo.error === null && cgo.stdout.trim() === '1';
    if (!fast && !raceAvailable) lines.push('  WARN  the race detector needs cgo (CGO_ENABLED is not 1 here); tests run without -race. Run them with -race on a machine with a C compiler or in CI');

    let failures = 0;
    for (const step of buildPlan({ fast, raceAvailable, configArgs })) {
        const result = run(step.tool, step.args, root);
        if (result.error !== null && result.error.code === 'ENOENT') {
            lines.push(`  MISS  ${step.label}: ${step.tool} is not installed (${INSTALL_HINTS[step.tool] ?? 'install it'})`);
            failures += 1;
            continue;
        }
        const output = `${result.stdout}${result.stderr}`;
        const passed = result.status === 0 && (step.cleanOutput !== true || output.trim() === '');
        if (passed) { lines.push(`  PASS  ${step.label}`); continue; }
        lines.push(`  FAIL  ${step.label}`, ...indent(output));
        failures += 1;
    }
    if (fast) lines.push('  skip  govulncheck and go test (--fast)');
    lines.push(failures === 0 ? 'go-check: ALL PASS' : `go-check: ${failures} FAIL`);
    return { exitCode: failures === 0 ? 0 : 1, lines };
}

function main(argv) {
    const fast = argv.includes('--fast');
    const directory = argv.find((arg) => !arg.startsWith('--')) ?? '.';
    const { exitCode, lines } = runGoCheck({ directory, fast });
    const stream = exitCode === 2 ? process.stderr : process.stdout;
    stream.write(`${lines.join('\n')}\n`);
    process.exitCode = exitCode;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main(process.argv.slice(2));
