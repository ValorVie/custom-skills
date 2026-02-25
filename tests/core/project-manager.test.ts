import { describe, expect, test } from "bun:test";
import { mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { initProject } from "../../src/core/project-manager";

describe("core/project-manager", () => {
  test("initProject copies template into target directory", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-project-"));
    const templateDir = join(root, "project-template");
    const targetDir = join(root, "target");

    try {
      await mkdir(join(templateDir, ".standards"), { recursive: true });
      await writeFile(join(templateDir, "README.md"), "template\n", "utf8");

      const result = await initProject({
        targetDir,
        templateDir,
        force: false,
      });

      expect(result.success).toBe(true);
      expect(result.copied).toBe(true);
      const content = await readFile(join(targetDir, "README.md"), "utf8");
      expect(content).toBe("template\n");
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("initProject skips when already initialized and force=false", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-project-"));
    const templateDir = join(root, "project-template");
    const targetDir = join(root, "target");

    try {
      await mkdir(join(templateDir, ".standards"), { recursive: true });
      await mkdir(join(targetDir, ".standards"), { recursive: true });

      const result = await initProject({
        targetDir,
        templateDir,
        force: false,
      });
      expect(result.success).toBe(true);
      expect(result.copied).toBe(false);
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });
});
