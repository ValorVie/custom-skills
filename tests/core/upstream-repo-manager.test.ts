import { describe, expect, test } from "bun:test";
import { mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import {
  addUpstreamRepo,
  analyzeRepositoryStructure,
  detectRepoFormat,
} from "../../src/core/upstream-repo-manager";

describe("core/upstream-repo-manager", () => {
  test("detectRepoFormat detects uds by .standards", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-upstream-format-uds-"));

    try {
      await mkdir(join(root, ".standards"), { recursive: true });
      const format = await detectRepoFormat(root);
      expect(format).toBe("uds");
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("detectRepoFormat detects claude-code-native by resource dirs", async () => {
    const root = await mkdtemp(
      join(tmpdir(), "ai-dev-upstream-format-native-"),
    );

    try {
      await mkdir(join(root, "skills"), { recursive: true });
      await mkdir(join(root, "commands"), { recursive: true });

      const format = await detectRepoFormat(root);
      expect(format).toBe("claude-code-native");
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("addUpstreamRepo writes upstream/sources.yaml", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-upstream-add-"));
    const configDir = join(root, "config");
    const repoDir = join(configDir, "example-repo");

    try {
      await mkdir(join(root, "upstream"), { recursive: true });
      await writeFile(
        join(root, "upstream", "sources.yaml"),
        "sources: {}\n",
        "utf8",
      );
      await mkdir(join(repoDir, ".standards"), { recursive: true });

      const result = await addUpstreamRepo({
        repoInput: "org/example-repo",
        branch: "main",
        skipClone: true,
        projectRoot: root,
        configDir,
      });

      expect(result.success).toBe(true);
      expect(result.format).toBe("uds");

      const sources = await readFile(
        join(root, "upstream", "sources.yaml"),
        "utf8",
      );
      expect(sources).toContain("example-repo:");
      expect(sources).toContain("repo: org/example-repo");
      expect(sources).toContain("format: uds");
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("addUpstreamRepo rejects duplicate source", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-upstream-dup-"));

    try {
      await mkdir(join(root, "upstream"), { recursive: true });
      await writeFile(
        join(root, "upstream", "sources.yaml"),
        "sources:\n  existing:\n    repo: org/existing\n    branch: main\n    local_path: ~/.config/existing/\n    format: uds\n    install_method: standards\n",
        "utf8",
      );

      const result = await addUpstreamRepo({
        repoInput: "org/existing",
        branch: "main",
        skipClone: true,
        projectRoot: root,
        configDir: join(root, "config"),
      });

      expect(result.success).toBe(false);
      expect(result.duplicate).toBe(true);
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("analyzeRepositoryStructure returns integration suggestion", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-upstream-analyze-"));

    try {
      await mkdir(join(root, "skills"), { recursive: true });
      const analysis = await analyzeRepositoryStructure(root);

      expect(analysis.hasSkills).toBe(true);
      expect(analysis.format).toBe("skills-repo");
      expect(analysis.recommendation.length).toBeGreaterThan(0);
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });
});
