import { describe, expect, test } from "bun:test";

import {
  BUN_PACKAGES,
  COPY_TARGETS,
  NPM_PACKAGES,
  REPOS,
} from "../../src/utils/shared";

describe("utils/shared", () => {
  test("NPM_PACKAGES includes OpenSpec", () => {
    expect(NPM_PACKAGES).toContain("@fission-ai/openspec@latest");
  });

  test("BUN_PACKAGES includes codex", () => {
    expect(BUN_PACKAGES).toContain("@openai/codex");
  });

  test("REPOS items include url and dir", () => {
    for (const repo of REPOS) {
      expect(repo.url.length > 0).toBe(true);
      expect(repo.dir.length > 0).toBe(true);
    }
  });

  test("COPY_TARGETS has Claude skills target", () => {
    const normalized = (COPY_TARGETS.claude.skills ?? "").replaceAll("\\", "/");
    expect(normalized.endsWith("/.claude/skills")).toBe(true);
  });
});
