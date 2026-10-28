import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { extractFrontmatter, parseFrontmatter } from "./frontmatter.js";
import type { MarketplaceData, MarketplacePlugin } from "../types.js";

export interface CrossValidationIssue {
  level: "error" | "warning";
  category: "marketplace-drift" | "orphan" | "companion" | "duplicate-desc" | "licence" | "version";
  skill: string;
  detail: string;
}

/**
 * Jaccard word-level similarity between two strings.
 * Returns 0.0 (completely different) to 1.0 (identical).
 */
export function jaccardSimilarity(a: string, b: string): number {
  const wordsA = new Set(a.toLowerCase().split(/\s+/).filter(Boolean));
  const wordsB = new Set(b.toLowerCase().split(/\s+/).filter(Boolean));

  if (wordsA.size === 0 && wordsB.size === 0) return 1.0;
  if (wordsA.size === 0 || wordsB.size === 0) return 0.0;

  let intersection = 0;
  for (const w of wordsA) {
    if (wordsB.has(w)) intersection++;
  }

  const union = wordsA.size + wordsB.size - intersection;
  return union === 0 ? 0 : intersection / union;
}

/**
 * Validate companion references in marketplace plugins.
 * Every companion must reference an existing plugin name.
 */
export function validateCompanions(plugins: MarketplacePlugin[]): CrossValidationIssue[] {
  const issues: CrossValidationIssue[] = [];
  const names = new Set(plugins.map((p) => p.name));

  for (const plugin of plugins) {
    for (const companion of plugin.metadata?.arcana?.companions ?? []) {
      if (!names.has(companion)) {
        issues.push({
          level: "error",
          category: "companion",
          skill: plugin.name,
          detail: `Companion "${companion}" does not exist in marketplace`,
        });
      }
    }
  }

  return issues;
}

/**
 * Check description sync between SKILL.md frontmatter and marketplace.json.
 * Returns an issue if similarity is below 0.5.
 */
export function validateDescriptionSync(
  skillName: string,
  frontmatterDesc: string,
  marketplaceDesc: string,
): CrossValidationIssue | null {
  if (!frontmatterDesc || !marketplaceDesc) return null;

  const similarity = jaccardSimilarity(frontmatterDesc, marketplaceDesc);
  if (similarity < 0.5) {
    return {
      level: "warning",
      category: "marketplace-drift",
      skill: skillName,
      detail: `Description drift (${Math.round(similarity * 100)}% similarity) between SKILL.md and marketplace.json`,
    };
  }

  return null;
}

const PROPRIETARY_REGEX = /all rights reserved/i;
const LICENCE_FILE_REGEX = /^(?:licen[cs]e|notice|copying)(?:\.[a-z]+)?$/i;

/**
 * Every skill in a published library ships under the repository licence. A skill-level licence
 * file, a license: field or a proprietary notice means third-party terms that licence does not
 * cover (docx and xlsx once carried Anthropic "All rights reserved" files in this Apache-2.0 repo).
 */
export function licenceIssues(skillDir: string, skill: string): CrossValidationIssue[] {
  const issues: CrossValidationIssue[] = [];
  const add = (detail: string): void => {
    issues.push({ level: "error", category: "licence", skill, detail });
  };
  const walk = (dir: string): void => {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const path = join(dir, entry.name);
      const shown = relative(skillDir, path).split("\\").join("/");
      if (entry.isDirectory()) {
        walk(path);
      } else if (LICENCE_FILE_REGEX.test(entry.name)) {
        add(`Skill-level licence file ${shown}: skills ship under the repository licence only`);
      } else if (PROPRIETARY_REGEX.test(readFileSync(path, "utf-8"))) {
        add(`Proprietary notice ("All rights reserved") in ${shown}`);
      }
    }
  };
  walk(skillDir);
  const skillMd = join(skillDir, "SKILL.md");
  const extracted = existsSync(skillMd) ? extractFrontmatter(readFileSync(skillMd, "utf-8")) : null;
  if (extracted && /^license:/m.test(extracted.raw)) {
    add("SKILL.md sets its own license: field; skills ship under the repository licence only");
  }
  return issues;
}

/**
 * Cross-validate skill directories against marketplace.json.
 * Checks: orphans, companions, description drift, licence, versions, near-duplicates.
 */
export function crossValidate(skillsDir: string, marketplacePath: string): CrossValidationIssue[] {
  const issues: CrossValidationIssue[] = [];

  // Load marketplace
  let marketplace: MarketplaceData;
  try {
    marketplace = JSON.parse(readFileSync(marketplacePath, "utf-8")) as MarketplaceData;
  } catch {
    issues.push({
      level: "error",
      category: "orphan",
      skill: "marketplace.json",
      detail: "Cannot read or parse marketplace.json",
    });
    return issues;
  }

  const pluginNames = new Set(marketplace.plugins.map((p) => p.name));
  const pluginMap = new Map(marketplace.plugins.map((p) => [p.name, p]));

  // Get skill directories
  let skillDirs: string[];
  try {
    skillDirs = readdirSync(skillsDir).filter((d) => {
      try {
        return statSync(join(skillsDir, d)).isDirectory();
      } catch {
        return false;
      }
    });
  } catch {
    issues.push({
      level: "error",
      category: "orphan",
      skill: "skills/",
      detail: "Cannot read skills directory",
    });
    return issues;
  }

  const dirNames = new Set(skillDirs);

  // 1. Orphan directories (dir exists, no marketplace entry)
  for (const dir of skillDirs) {
    if (!pluginNames.has(dir)) {
      issues.push({
        level: "error",
        category: "orphan",
        skill: dir,
        detail: "Skill directory exists but no marketplace.json entry",
      });
    }
  }

  // 2. Orphan entries (marketplace entry, no dir)
  for (const name of pluginNames) {
    if (!dirNames.has(name)) {
      issues.push({
        level: "error",
        category: "orphan",
        skill: name,
        detail: "Marketplace entry exists but no skill directory",
      });
    }
  }

  // 3. Companion validation
  issues.push(...validateCompanions(marketplace.plugins));

  // 4. Description drift (SKILL.md frontmatter vs marketplace.json)
  for (const dir of skillDirs) {
    const plugin = pluginMap.get(dir);
    if (!plugin) continue;

    const skillMd = join(skillsDir, dir, "SKILL.md");
    if (!existsSync(skillMd)) continue;

    try {
      const content = readFileSync(skillMd, "utf-8");
      const extracted = extractFrontmatter(content);
      if (!extracted) continue;
      const parsed = parseFrontmatter(extracted.raw);
      if (!parsed?.description) continue;

      const driftIssue = validateDescriptionSync(dir, parsed.description, plugin.description);
      if (driftIssue) issues.push(driftIssue);
    } catch {
      /* skip unreadable */
    }
  }

  // 5. Licence: a published skill must be ours to ship under the repo licence
  for (const dir of skillDirs) issues.push(...licenceIssues(join(skillsDir, dir), dir));

  // 6. Versions: Claude Code treats an entry version as the update signal, so they move together
  const releaseVersion = marketplace.metadata?.version;
  for (const plugin of marketplace.plugins) {
    if (plugin.version !== releaseVersion) {
      issues.push({
        level: "error",
        category: "version",
        skill: plugin.name,
        detail: `Entry version ${plugin.version} differs from metadata.version ${String(releaseVersion)}`,
      });
    }
  }

  // 7. Near-duplicate descriptions across skills
  const descriptions = marketplace.plugins.map((p) => ({ name: p.name, desc: p.description }));
  for (let i = 0; i < descriptions.length; i++) {
    for (let j = i + 1; j < descriptions.length; j++) {
      const a = descriptions[i]!;
      const b = descriptions[j]!;
      const sim = jaccardSimilarity(a.desc, b.desc);
      if (sim > 0.85) {
        issues.push({
          level: "warning",
          category: "duplicate-desc",
          skill: a.name,
          detail: `Near-duplicate description with ${b.name} (${Math.round(sim * 100)}% similarity)`,
        });
      }
    }
  }

  return issues;
}
