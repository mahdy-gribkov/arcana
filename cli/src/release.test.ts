import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const read = (path: string): unknown =>
  JSON.parse(readFileSync(fileURLToPath(new URL(path, import.meta.url)), "utf-8"));

// The marketplace version is the update signal for Claude Code users and the CLI version is the
// npm release; marketplace.json once sat at 3.0.0 while the CLI shipped 4.0.0.
describe("release versions", () => {
  it("marketplace metadata.version equals the CLI package version", () => {
    const manifest = read("../../.claude-plugin/marketplace.json") as { metadata: { version: string } };
    const cli = read("../package.json") as { version: string };

    expect(manifest.metadata.version).toBe(cli.version);
  });
});
