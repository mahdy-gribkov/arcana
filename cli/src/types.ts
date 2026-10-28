export interface SkillInfo {
  name: string;
  description: string;
  version: string;
  source: string;
  repo?: string;
  tags?: string[];
  conflicts?: string[];
  companions?: string[];
  verified?: boolean;
  author?: string;
}

export interface SkillFile {
  path: string;
  content: string;
}

/** Claude Code marketplace.json (code.claude.com/docs/en/plugins/marketplace-reference). */
export interface MarketplaceData {
  name: string;
  owner?: { name: string; email?: string; url?: string };
  metadata?: { description?: string; version?: string };
  plugins: MarketplacePlugin[];
}

export interface MarketplacePlugin {
  name: string;
  source: string;
  description: string;
  version: string;
  tags?: string[];
  author?: { name: string; email?: string; url?: string };
  /** Free-form per-entry object that Claude Code ignores; Arcana keeps its relations here. */
  metadata?: { arcana?: { companions?: string[]; conflicts?: string[] } };
}

export interface ProviderConfig {
  name: string;
  type: string;
  url: string;
  enabled: boolean;
}

export interface ArcanaConfig {
  defaultProvider: string;
  installDir: string;
  providers: ProviderConfig[];
}

export interface SkillFrontmatter {
  name: string;
  description: string;
}

export interface ValidationResult {
  skill: string;
  valid: boolean;
  errors: string[];
  warnings: string[];
  infos: string[];
  fixed?: boolean;
}

export interface SkillMeta {
  version: string;
  installedAt: string;
  source: string;
  description?: string;
  fileCount?: number;
  sizeBytes?: number;
}

export interface DoctorCheck {
  name: string;
  status: "pass" | "warn" | "fail";
  message: string;
  fix?: string;
}
