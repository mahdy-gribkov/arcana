import { isSkillInstalled } from "../utils/fs.js";

// Category map: every skill in skills/ appears exactly once (categories.test.ts enforces it).
const SKILL_CATEGORIES: Record<string, string[]> = {
  "Code Quality & Review": ["codebase-analysis", "testing", "git-workflow", "performance-optimization", "design-doc"],
  Security: ["security-review", "bugbounty-report", "oauth-auth"],
  "Languages & Frameworks": ["ts-dev", "go-dev", "python-best-practices", "nextjs-16", "tailwind-css"],
  "APIs, Data & AI": ["api-design", "database-design", "llm-integration", "scraping-automation"],
  Infrastructure: ["docker-kubernetes", "ci-cd-pipelines"],
  "Web Quality": ["accessibility-wcag", "i18n-localization", "seo-meta"],
};

export { SKILL_CATEGORIES };

export function getCategoryFor(skillName: string): string | undefined {
  for (const [cat, skills] of Object.entries(SKILL_CATEGORIES)) {
    if (skills.includes(skillName)) return cat;
  }
  return undefined;
}

export function getRelatedSkills(skillName: string, limit = 3): string[] {
  const cat = getCategoryFor(skillName);
  if (!cat) return [];
  return (SKILL_CATEGORIES[cat] ?? []).filter((s) => s !== skillName && !isSkillInstalled(s)).slice(0, limit);
}
