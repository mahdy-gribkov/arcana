import { describe, it, expect } from "vitest";
import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { COMMANDS } from "./command-defs.js";

// Regression: the README advertised 74 skills and commands that do not exist (hook, snapshot,
// trim, benchmark, profile, team) long after the code changed.
const ROOT = fileURLToPath(new URL("../../", import.meta.url));
const readme = readFileSync(join(ROOT, "README.md"), "utf-8");
const skills = readdirSync(join(ROOT, "skills"), { withFileTypes: true })
  .filter((d) => d.isDirectory() && existsSync(join(ROOT, "skills", d.name, "SKILL.md")))
  .map((d) => d.name);
const commandNames = new Set(COMMANDS.map((c) => c.command.split(" ")[0]));

describe("README matches the code", () => {
  it("names every skill and states the real count", () => {
    expect(skills.filter((name) => !readme.includes(`\`${name}\``))).toEqual([]);
    expect(readme).toContain(`${skills.length} focused, tested skills`);
  });

  it("shows only registered commands", () => {
    const shown = [...readme.matchAll(/\barcana ([a-z]+)/g)].map((m) => m[1]!);
    expect(shown.filter((name) => !commandNames.has(name))).toEqual([]);
  });
});
