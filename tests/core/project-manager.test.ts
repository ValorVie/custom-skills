import { describe, expect, test } from "bun:test";
import { mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { initProject, updateProject } from "../../src/core/project-manager";

describe("core/project-manager", () => {
  test("initProject returns failure when template directory is missing", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-project-"));
    const targetDir = join(root, "target");
    const templateDir = join(root, "missing-template");

    try {
      const result = await initProject({
        targetDir,
        templateDir,
        force: false,
      });

      expect(result.success).toBe(false);
      expect(result.copied).toBe(false);
      expect(result.message).toBe("template directory not found");
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

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

  test("initProject with force=true copies template even when already initialized", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-project-"));
    const templateDir = join(root, "project-template");
    const targetDir = join(root, "target");

    try {
      await mkdir(join(templateDir, ".standards"), { recursive: true });
      await mkdir(join(targetDir, ".standards"), { recursive: true });
      await writeFile(join(templateDir, "README.md"), "template\n", "utf8");
      await writeFile(join(targetDir, "README.md"), "existing\n", "utf8");

      const result = await initProject({
        targetDir,
        templateDir,
        force: true,
      });

      expect(result.success).toBe(true);
      expect(result.copied).toBe(true);
      const content = await readFile(join(targetDir, "README.md"), "utf8");
      expect(content).toBe("template\n");
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("updateProject runs only openspec when requested", async () => {
    const called: string[] = [];
    const result = await updateProject({
      only: "openspec",
      deps: {
        runCommandFn: async (command: string[]) => {
          called.push(command[0]);
          return { stdout: "", stderr: "", exitCode: 0 };
        },
      },
    });

    expect(called).toEqual(["openspec"]);
    expect(result.openspec).toBe(true);
    expect(result.uds).toBeUndefined();
    expect(result.errors).toEqual([]);
  });

  test("updateProject collects failures from both commands", async () => {
    const result = await updateProject({
      deps: {
        runCommandFn: async (command: string[]) => {
          if (command[0] === "openspec") {
            return { stdout: "", stderr: "", exitCode: 0 };
          }
          return { stdout: "", stderr: "failed", exitCode: 1 };
        },
      },
    });

    expect(result.openspec).toBe(true);
    expect(result.uds).toBe(false);
    expect(result.errors).toEqual(["uds update failed"]);
  });
});
