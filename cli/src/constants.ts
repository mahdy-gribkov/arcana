// Retention & pruning
export const AGENT_LOG_MAX_AGE_DAYS = 7;
export const MAIN_LOG_MAX_AGE_DAYS = 30;
export const STALE_PROJECT_DAYS = 90;
export const PRUNE_DEFAULT_DAYS = 14;
export const PRUNE_SIZE_THRESHOLD_BYTES = 10 * 1024 * 1024; // 10 MB
export const PRUNE_KEEP_NEWEST = 3;

// Skill size warnings
export const LARGE_SKILL_KB_THRESHOLD = 50;
export const TOKENS_PER_KB = 256;
export const CONTEXT_WINDOW_TOKENS = 200_000;

// Progressive disclosure
export const INDEX_FILENAME = "_index.md";
export const LOADED_FILENAME = "_loaded.md";
export const ACTIVE_FILENAME = "_active.md";

// Context curation budget
export const CONTEXT_BUDGET_PCT = 30; // Max % of model context for skills
export const MODEL_CONTEXTS: Record<string, number> = {
  // Claude (March 2026): 200K standard, 1M beta for Opus/Sonnet
  "claude-opus-4.6": 200_000,
  "claude-sonnet-4.6": 200_000,
  "claude-haiku-4.5": 200_000,
  // OpenAI (March 2026)
  "gpt-5.4": 1_000_000,
  // Google Gemini (March 2026)
  "gemini-3.1-pro": 1_000_000,
  "gemini-3.1-flash": 1_000_000,
  "gemini-3.1-thinking": 1_000_000,
  default: 200_000,
};

// Official skill repository: the one home for its location (provider, default config, help text).
export const OFFICIAL_REPO = { owner: "mahdy-gribkov", name: "arcana", branch: "master" } as const;
export const OFFICIAL_REPO_SLUG = `${OFFICIAL_REPO.owner}/${OFFICIAL_REPO.name}`;
/** Earlier homes of the official repo; a saved config that still names one is read as OFFICIAL_REPO_SLUG. */
export const RETIRED_REPO_SLUGS: readonly string[] = ["medy-gribkov/arcana"];

// Validation
/** Agent Skills spec: 1-64 chars, lowercase letters and digits, single hyphens, no hyphen at either end. */
export const SKILL_NAME_REGEX = /^(?=.{1,64}$)[a-z0-9]+(?:-[a-z0-9]+)*$/;
/** Agent Skills spec limit for SKILL.md; detail beyond it belongs in references/. */
export const SKILL_MAX_LINES = 500;
export const JACCARD_THRESHOLD = 0.5;

// Cache
export const CACHE_MAX_AGE_MS = 24 * 60 * 60 * 1000; // 24 hours

// Diagnostics thresholds
export const MEMORY_MAX_LINES = 200;
export const AGENT_BLOAT_PERCENT = 70;
export const DISK_WARN_BYTES = 1 * 1024 * 1024 * 1024; // 1 GB

// Display
export const DESCRIPTION_TRUNCATION = 50;
