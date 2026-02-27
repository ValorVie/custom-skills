import { describe, expect, test } from "bun:test";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { initProject } from "../../src/core/project-manager";

describe("core/project-manager reverse sync", () => {
  test("reverse sync requires force=true", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-project-reverse-sync-"));
    const projectDir = join(root, "custom-skills");
    const templateDir = join(projectDir, "project-template");
    const previousCwd = process.cwd();

    try {
      await mkdir(projectDir, { recursive: true });
      await mkdir(templateDir, { recursive: true });
      await writeFile(join(templateDir, "README.md"), "template\n", "utf8");
      await writeFile(join(projectDir, "README.md"), "project\n", "utf8");

      process.chdir(projectDir);

      const withoutForce = await initProject({
        targetDir: projectDir,
        templateDir,
        force: false,
      });
      expect(withoutForce.reverseSynced).toBe(false);

      const withForce = await initProject({
        targetDir: projectDir,
        templateDir,
        force: true,
      });
      expect(withForce.reverseSynced).toBe(true);
    } finally {
      process.chdir(previousCwd);
      await rm(root, { recursive: true, force: true });
    }
  });
});
