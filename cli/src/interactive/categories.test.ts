import { describe, it, expect } from "vitest";
import { existsSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { SKILL_CATEGORIES } from "./categories.js";
import { SKILL_SUGGESTIONS, SKILL_SUGGESTIONS_DEFAULT } from "../commands/init.js";

// Regression: these hand-kept name lists drifted to skills that never existed or were deleted
// (codebase-dissection, golang-pro, docx). Every name must be a real folder in skills/.
const SKILLS_DIR = fileURLToPath(new URL("../../../skills", import.meta.url));
const repoSkills = readdirSync(SKILLS_DIR, { withFileTypes: true })
  .filter((d) => d.isDirectory() && existsSync(join(SKILLS_DIR, d.name, "SKILL.md")))
  .map((d) => d.name)
  .sort();

describe("skill name lists match skills/", () => {
  it("lists every repo skill in exactly one category", () => {
    const categorized = Object.values(SKILL_CATEGORIES).flat().sort();
    expect(categorized).toEqual(repoSkills);
  });

  it("suggests only skills that exist", () => {
    const suggested = new Set([...Object.values(SKILL_SUGGESTIONS).flat(), ...SKILL_SUGGESTIONS_DEFAULT]);
    expect([...suggested].filter((name) => !repoSkills.includes(name))).toEqual([]);
  });
});
