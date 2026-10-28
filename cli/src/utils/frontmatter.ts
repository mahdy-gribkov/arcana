import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { parseDocument, stringify } from "yaml";
import { SKILL_MAX_LINES, SKILL_NAME_REGEX } from "../constants.js";
import type { SkillFrontmatter, ValidationResult } from "../types.js";

const FM_DELIMITER = "---";
export const MIN_DESC_LENGTH = 80;
export const MAX_DESC_LENGTH = 1024;
const USE_WHEN_REGEX = /\buse (?:this skill )?when\b/i;

/** Agent Skills spec fields plus the Claude Code extensions. */
const OPTIONAL_FIELDS = [
  "license",
  "compatibility",
  "metadata",
  "allowed-tools",
  "argument-hint",
  "disable-model-invocation",
  "user-invocable",
  "model",
  "context",
];
const MISSPELLED_FIELDS: Record<string, string> = { "user-invokable": "user-invocable" };

export function extractFrontmatter(content: string): { raw: string; body: string } | null {
  // CRLF files (any Windows checkout) would leave a "\r" on each line that strict YAML rejects.
  const lines = content.split(/\r?\n/);
  if (lines[0]?.trim() !== FM_DELIMITER) return null;

  let endIdx = -1;
  for (let i = 1; i < lines.length; i++) {
    if (lines[i]?.trim() === FM_DELIMITER) {
      endIdx = i;
      break;
    }
  }

  if (endIdx < 0) return null;

  const raw = lines.slice(1, endIdx).join("\n");
  const body = lines.slice(endIdx + 1).join("\n");
  return { raw, body };
}

export type FrontmatterParse = { ok: true; fields: Record<string, unknown> } | { ok: false; error: string };

/**
 * Parses frontmatter as strict YAML. Agents load SKILL.md with a real YAML parser, so anything a
 * lenient line-matcher accepts but YAML rejects (an unquoted "Use when: ...") loads with no fields.
 */
export function parseFrontmatterYaml(raw: string): FrontmatterParse {
  const doc = parseDocument(raw, { prettyErrors: false, uniqueKeys: true });
  const firstError = doc.errors[0];
  if (firstError) return { ok: false, error: firstError.message.split("\n")[0] ?? firstError.message };
  const fields: unknown = doc.toJS();
  if (!isMapping(fields)) return { ok: false, error: "Frontmatter is not a YAML mapping" };
  return { ok: true, fields };
}

function isMapping(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

export function parseFrontmatter(raw: string): SkillFrontmatter | null {
  const parsed = parseFrontmatterYaml(raw);
  if (!parsed.ok) return null;
  const { name, description } = parsed.fields;
  if (typeof name !== "string" || !SKILL_NAME_REGEX.test(name)) return null;
  return { name, description: typeof description === "string" ? description.trim() : "" };
}

export function fixSkillFrontmatter(content: string): string {
  const extracted = extractFrontmatter(content);
  if (!extracted) return content;

  const parsed = parseFrontmatter(extracted.raw);
  if (!parsed) return content;

  // Rebuild clean frontmatter with only name and description; the serializer quotes when YAML needs it.
  const yamlText = stringify({ name: parsed.name, description: parsed.description }, { lineWidth: 0 });
  return `${FM_DELIMITER}\n${yamlText}${FM_DELIMITER}\n` + extracted.body.replace(/^\n+/, "\n");
}

function referencesHaveCode(skillDir: string): boolean {
  const refs = join(skillDir, "references");
  if (!existsSync(refs)) return false;
  return readdirSync(refs)
    .filter((file) => file.endsWith(".md"))
    .some((file) => readFileSync(join(refs, file), "utf-8").includes("```"));
}

export function validateSkillDir(skillDir: string, skillName: string): ValidationResult {
  const result: ValidationResult = {
    skill: skillName,
    valid: true,
    errors: [],
    warnings: [],
    infos: [],
  };

  const skillMd = join(skillDir, "SKILL.md");
  if (!existsSync(skillMd)) {
    result.valid = false;
    result.errors.push("Missing SKILL.md");
    return result;
  }

  let content: string;
  try {
    content = readFileSync(skillMd, "utf-8");
  } catch {
    result.valid = false;
    result.errors.push("Cannot read SKILL.md");
    return result;
  }

  const extracted = extractFrontmatter(content);
  if (!extracted) {
    result.valid = false;
    result.errors.push("Missing or malformed frontmatter delimiters (---)");
    return result;
  }

  const yamlParse = parseFrontmatterYaml(extracted.raw);
  if (!yamlParse.ok) {
    result.valid = false;
    result.errors.push(`Frontmatter is not valid YAML: ${yamlParse.error}. Quote values that contain ": ".`);
    return result;
  }

  const parsed = parseFrontmatter(extracted.raw);
  if (!parsed) {
    result.valid = false;
    result.errors.push("Cannot parse name from frontmatter (lowercase letters, digits and hyphens)");
    return result;
  }

  if (!parsed.description) {
    result.valid = false;
    result.errors.push("Missing description in frontmatter");
  } else if (parsed.description.length < MIN_DESC_LENGTH) {
    result.valid = false;
    result.errors.push(`Description too short (${parsed.description.length} chars, minimum ${MIN_DESC_LENGTH})`);
  } else if (parsed.description.length > MAX_DESC_LENGTH) {
    result.valid = false;
    result.errors.push(`Description too long (${parsed.description.length} chars, max ${MAX_DESC_LENGTH})`);
  } else if (!USE_WHEN_REGEX.test(parsed.description)) {
    result.valid = false;
    result.errors.push('Description has no "Use when" clause (agents pick skills by it)');
  }

  for (const key of Object.keys(yamlParse.fields)) {
    if (key === "name" || key === "description") continue;
    if (MISSPELLED_FIELDS[key]) {
      result.warnings.push(`Misspelled field: ${key} (use ${MISSPELLED_FIELDS[key]})`);
    } else if (OPTIONAL_FIELDS.includes(key)) {
      result.infos.push(`Optional field: ${key}`);
    } else {
      result.infos.push(`Non-standard field: ${key}`);
    }
  }

  const lineCount = content.split("\n").length;
  if (lineCount > SKILL_MAX_LINES) {
    result.valid = false;
    result.errors.push(`SKILL.md has ${lineCount} lines (max ${SKILL_MAX_LINES}); move detail into references/`);
  }

  if (parsed.name !== skillName) {
    result.warnings.push(`Name mismatch: frontmatter says "${parsed.name}", directory is "${skillName}"`);
  }

  if (parsed.description && (parsed.description.startsWith('"') || parsed.description.startsWith("'"))) {
    result.warnings.push("Description starts with a quote character (likely a YAML quoting issue)");
  }

  if (extracted.body.trim().length < 50) {
    result.warnings.push("SKILL.md body is very short (less than 50 chars)");
  }

  if (extracted.body.trim().length >= 50 && !extracted.body.includes("##")) {
    result.warnings.push("Body has no ## headings (required for structure)");
  }

  // Check for code blocks (quality signal); a router SKILL.md may keep its examples in references/
  if (extracted.body.trim().length >= 50 && !extracted.body.includes("```") && !referencesHaveCode(skillDir)) {
    result.warnings.push("No code blocks found in SKILL.md or references/ (skills must include code examples)");
  }

  // Check for BAD/GOOD pattern examples
  const hasPattern =
    /(?:BAD|GOOD|WRONG|RIGHT|AVOID|PREFER|DO NOT|INSTEAD)/i.test(extracted.body) ||
    /<!--\s*(?:bad|good)\s*-->/i.test(extracted.body);
  if (extracted.body.trim().length >= 100 && !hasPattern) {
    result.infos.push("No BAD/GOOD contrast patterns found (recommended for teaching)");
  }

  if (result.errors.length > 0) result.valid = false;

  return result;
}
