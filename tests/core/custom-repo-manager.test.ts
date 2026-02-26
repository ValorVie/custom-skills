import { describe, expect, test } from "bun:test";
import { mkdir, mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import {
  fixRepoStructure,
  validateRepoStructure,
} from "../../src/core/custom-repo-manager";

describe("core/custom-repo-manager", () => {
  test("validateRepoStructure reports invalid when no expected directories", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-custom-repo-validate-"));

    try {
      const result = await validateRepoStructure(root);
      expect(result.valid).toBe(false);
      expect(result.existing.length).toBe(0);
      expect(result.missing).toContain("skills");
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("validateRepoStructure is valid when skills directory exists", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-custom-repo-valid-"));

    try {
      await mkdir(join(root, "skills"), { recursive: true });

      const result = await validateRepoStructure(root);
      expect(result.valid).toBe(true);
      expect(result.existing).toContain("skills");
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("fixRepoStructure creates missing standard directories", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-custom-repo-fix-"));

    try {
      const fixed = await fixRepoStructure(root);
      expect(fixed.created.length).toBeGreaterThan(0);

      const result = await validateRepoStructure(root);
      expect(result.valid).toBe(true);
      expect(result.existing).toContain("skills");
      expect(result.existing).toContain("commands");
      expect(result.existing).toContain("agents");
      expect(result.existing).toContain("workflows");
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });
});
